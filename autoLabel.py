from typing import Tuple
from pathlib import Path
import itertools

from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QFileDialog, QGraphicsItem, QMenu, QAction, QMessageBox
from PyQt5.QtGui import QKeyEvent, QPixmap, QImage
from PyQt5.QtCore import Qt, QPointF, QPoint
import cv2

from utils.SAM import SA
from utils.format import AutoLabelFormat
from utils.classSelectionDialog import load_classes_from_file, create_class_index_dictionary
from utils.general import Data, parse_yolo, parse_xml, parse_coco, to_orig_pos, to_scaled_pos, save_yolo_format, save_pascal_format, save_coco_format, track_changes
import autoLabel_ui as ui


class AutoLabel(QtWidgets.QMainWindow, ui.Ui_AutoLabel):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        load_classes_from_file("classes.txt")
        self.sam = SA(model_name="vit_b", model_path="sam_vit_b_01ec64.pth")

        self.pixmap = None
        self.current_image_index = 0
        btn_cycle_texts = itertools.cycle([member.name for member in AutoLabelFormat])
        self.classes_mapping = create_class_index_dictionary()

        self.openFileBtn.clicked.connect(self.open_file)
        self.openDirBtn.clicked.connect(self.open_dir)
        self.nextImageBtn.clicked.connect(self.next_img)
        self.prevImageBtn.clicked.connect(self.prev_img)
        self.predBtn.clicked.connect(lambda: self.predict_event())
        self.changeFormatBtn.clicked.connect(lambda: self.change_save_format(next(btn_cycle_texts)))
        self.saveBtn.clicked.connect(lambda: self.save(self.get_save_format()))
        self.classList.itemClicked.connect(self.highlight_clicked_item)
        self.classList.customContextMenuRequested.connect(self.show_tool_menu)
        self.fileList.itemDoubleClicked.connect(lambda item: self.switch_img(self.fileList.row(item)))

    # override
    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key_D:
            self.next_img()
        elif event.key() == Qt.Key_A:
            self.prev_img()
        elif event.key() == Qt.Key_Delete:
            self.delete_event()
        elif event.key() == Qt.Key_Space:
            self.predict_event()
        elif event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_S:
            self.save(self.get_save_format())
    
        return super().keyPressEvent(event)


    def open_file(self) -> None:
        if self.confirm_modified():
            self.current_image_index = 0  # initial index

            file_path, _ = QFileDialog.getOpenFileName(None, "Select file", "", "Image Files (*.jpg;*.jpeg;*.png;*.bmp;)")
            if file_path:
                self.show_file_path([file_path])
                self.show_image(self.current_image_index)


    def open_dir(self) -> None:
        if self.confirm_modified():
            self.current_image_index = 0  # initial index

            folder_path = QFileDialog.getExistingDirectory(self, "Open folder", "./")
            if folder_path:
                extensions = ["*.jpg", "*.jpeg", "*.png", "*.bmp"]
                files = []
                for ext in extensions:
                    files.extend(Path(folder_path).glob(ext))

                if files:
                    self.show_file_path([str(img) for img in files])
                    self.show_image(self.current_image_index)


    def show_file_path(self, file_path: list) -> None:
        self.fileList.clear()
        self.fileList.addItems(file_path)
        self.fileList.setCurrentItem(self.fileList.item(0))


    def show_image(self, index: int) -> None:
        image = cv2.imread(self.fileList.item(index).text())
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        height, width, channel = image.shape

        bytesPerLine = 3 * width
        self.pixmap = QPixmap.fromImage(QImage(image, width, height, bytesPerLine, QImage.Format_RGB888))

        self.graphicsView.set_class_list(self.classList)
        self.graphicsView.set_pixmap(self.pixmap)
        self.show_boxes(Path(self.fileList.item(index).text()))
    

    def show_boxes(self, file_path: Path) -> None:
        scaled_pixmap_size = self.graphicsView.get_scaled_pixmap().size()
        ori_pixmap_size = self.pixmap.size()
        scaled_h = scaled_pixmap_size.height()
        scaled_w = scaled_pixmap_size.width()

        boxes = []
        if file_path.with_suffix(".txt").exists():
            boxes = parse_yolo(str(file_path.with_suffix(".txt")), scaled_h, scaled_w)
        elif file_path.with_suffix(".xml").exists():
            boxes = parse_xml(str(file_path.with_suffix(".xml")), scaled_pixmap_size, ori_pixmap_size)
        elif Path("annotations.json").exists():
            boxes = parse_coco(str(file_path.parent / "annotations.json"), file_path.name, self.classes_mapping, scaled_pixmap_size, ori_pixmap_size)

        self.add_rects(boxes)


    def next_img(self) -> None:
        if self.confirm_modified():
            if self.current_image_index+1 < len(self.fileList):
                self.current_image_index += 1
                self.switch_img(self.current_image_index)


    def prev_img(self) -> None:
        if self.confirm_modified():
            if self.current_image_index-1 >= 0:
                self.current_image_index -= 1
                self.switch_img(self.current_image_index)


    def switch_img(self, index: int) -> None:
        if self.confirm_modified():
            self.current_image_index = index
            self.show_image(index)
            self.fileList.setCurrentRow(index)


    @track_changes
    def predict_event(self) -> None:
        if self.pixmap is not None:
            scaled_size = self.graphicsView.get_scaled_pixmap().size()
            ori_size = self.pixmap.size()

            labels, points = self.get_starts_label_coords()
            if labels and points:
                image_path = self.fileList.currentItem().text()
                x, y, w, h = self.sam.predict_box(image_path, points, labels)

                topLeftPos = to_scaled_pos(x, y, scaled_size, ori_size)
                bottomRightPos = to_scaled_pos(x+w, y+h, scaled_size, ori_size)
                self.graphicsView.scene().add_rect(QPointF(topLeftPos), QPointF(bottomRightPos))


    @track_changes
    def delete_event(self) -> None:
        list_item = self.classList.currentItem()
        if list_item is not None:
            self.delete_item(list_item)
            self.unsetCursor()


    def get_starts_label_coords(self) -> Tuple[list, list]:
        label_mapping = {"red": 0, "green": 1}
        labels, points = [], []
        deletable_items = []

        for row in range(self.classList.count()):
            item = self.classList.item(row)
            text = item.text()
            if text in label_mapping:
                item_pos = item.data(Qt.UserRole).scenePos()
                o_x, o_y = to_orig_pos(item_pos, self.graphicsView.get_scaled_pixmap().size(), self.pixmap.size())

                labels.append(label_mapping[text])
                points.append([o_x, o_y])
                
                deletable_items.append(item)

        for item in deletable_items:
            self.delete_item(item)

        return labels, points


    def confirm_modified(self) -> bool:
        if Data.is_modified:
            reply = QMessageBox.warning(self, "Attention", "You have unsaved changes, process anyway?", QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                Data.is_modified = False
                return True
            else:
                return False
        
        Data.is_modified = False
        return True


    def add_rects(self, boxes: list):
        for classes, topLeft, bottomRight in boxes:
                self.graphicsView.scene().add_rect(QPointF(topLeft), QPointF(bottomRight), classes)


    def highlight_clicked_item(self) -> None:
        self.graphicsView.scene().clearSelection()

        list_item = self.classList.currentItem()
        box_item = list_item.data(Qt.UserRole)
        box_item.setSelected(True)
        self.set_item_to_Top(box_item)

        self.graphicsView.scene().update()


    def set_item_to_Top(self, item: QGraphicsItem) -> None:
        z_values = [box.zValue() for box in self.graphicsView.scene().items()]
        item.setZValue(max(z_values) + 1)
        

    def show_tool_menu(self, pos: QPoint) -> None:
        item = self.classList.itemAt(pos)
        if item is not None:
            menu = QMenu(self.classList)

            delete_action = QAction("Delete", self.classList)
            delete_action.triggered.connect(lambda: self.delete_event())
            menu.addAction(delete_action)

            if item.text() not in ["red", "green"]:
                class_action = QAction("Edit Class", self.classList)
                class_action.triggered.connect(lambda: self.edit_item_class(item))
                menu.addAction(class_action)

            menu.exec_(self.classList.mapToGlobal(pos))
    

    def delete_item(self, item: QGraphicsItem) -> None:
        box_item = item.data(Qt.UserRole)
        self.graphicsView.scene().removeItem(box_item)
        self.classList.takeItem(self.classList.row(item))
    

    @track_changes
    def edit_item_class(self, item: QGraphicsItem) -> None:
        box_item = item.data(Qt.UserRole)
        selected_classes = self.graphicsView.scene().selectClass_Dialog()
        box_item.classes = selected_classes
        item.setText(selected_classes)


    def change_save_format(self, format: str) -> None:
        self.changeFormatBtn.setText(format)


    def get_save_format(self) -> AutoLabelFormat:
        format = self.changeFormatBtn.text()
        if format == AutoLabelFormat.YOLO.name:
            return AutoLabelFormat.YOLO
        elif format == AutoLabelFormat.PascalVOC.name:
            return AutoLabelFormat.PascalVOC
        elif format == AutoLabelFormat.COCO.name:
            return AutoLabelFormat.COCO
        

    def save(self, format=None) -> None:
        if self.pixmap is not None:
            scaled_size = self.graphicsView.get_scaled_pixmap().size()
            ori_size = self.pixmap.size()
            file_path = Path(self.fileList.currentItem().text())
            options = QFileDialog.Options()
            
            if format == AutoLabelFormat.YOLO:
                save_yolo_format(file_path, self.classList, self.classes_mapping, scaled_size, options)
            elif format == AutoLabelFormat.PascalVOC:
                save_pascal_format(file_path, self.classList, self.classes_mapping, scaled_size, ori_size, options)
            elif format == AutoLabelFormat.COCO:
                save_coco_format(file_path, self.classList, self.classes_mapping, scaled_size, ori_size, options)

            Data.is_modified = False

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    ui = AutoLabel()
    ui.show()
    sys.exit(app.exec_())