from typing import Tuple

from PyQt5 import QtGui, QtWidgets
from PyQt5.QtWidgets import QListWidget, QGraphicsPixmapItem, QGraphicsItem, QListWidgetItem, QDialog
from PyQt5.QtGui import QCursor
from PyQt5.QtCore import Qt, QRectF, QPointF
from PyQt5.QtWidgets import QGraphicsSceneMouseEvent

from utils.classSelectionDialog import CategoryDialog
from graphics.graphicsItems import AlRectItem, AlStartItem


class AlGraphicsScene(QtWidgets.QGraphicsScene):
    def __init__(self, parent=None, class_list: QListWidget=None) -> None:
        super().__init__(parent=parent)
        self.class_list = class_list

        # drawing
        self.mouse_start_pos = None
        self.temp_item = None

        # pixmap
        self.pixmap_item = None
        self.pixmap_scene_rect = None

        # dragging
        self.selected_item = None 
        self.dragging = False

        # scaling
        self.scaling = False

    # override
    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        if event.button() != Qt.LeftButton:
            return
        
        if QCursor().shape() == Qt.PointingHandCursor:
            self.scaling = True

        item = self.itemAt(event.scenePos(), QtGui.QTransform())
        if item is not None and isinstance(item, (AlRectItem, AlStartItem)):
            self.selected_item = item
            self.dragging = True
        
            for row in range(self.class_list.count()):  # highlight label of selected item 
                row_item = self.class_list.item(row)
                if row_item.data(Qt.UserRole) == self.selected_item:
                    self.class_list.setCurrentRow(row)
                    break
        elif isinstance(item, QGraphicsPixmapItem):
            self.mouse_start_pos = event.scenePos()
            self.temp_item = AlRectItem()
            self.temp_item.setParentItem(self.pixmap_item)
        else:
            self.clearSelection()

        self.update()
        return super().mousePressEvent(event)

    # override
    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        if self.temp_item:   # painting
            rect, intersect_rect = self.get_rects(self.mouse_start_pos, event.scenePos())
            self.temp_item.setRect(intersect_rect if not self.pixmap_scene_rect.contains(event.scenePos()) else rect)    # prevent out of bounds
        
        self.update()
        return super().mouseMoveEvent(event)
    
    # override
    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        if event.button() == Qt.RightButton:
            self.right_click_event(event)
        elif event.button() == Qt.LeftButton:       
            self.left_click_event(event)
        
        self.update()
        return super().mouseReleaseEvent(event)

    def right_click_event(self, event: QGraphicsSceneMouseEvent) -> None:
        mouse_pos = event.scenePos()
        if self.pixmap_scene_rect.contains(mouse_pos):
            start_item = self.create_startItem("red", mouse_pos)
            start_item.setParentItem(self.pixmap_item)

    def left_click_event(self, event: QGraphicsSceneMouseEvent) -> None:
        if self.dragging:
            self.selected_item.setSelected(False)
            self.selected_item = None
            self.dragging = False
            self.scaling = False
        elif self.temp_item:
            area = self.calculate_area(self.temp_item.rect())
            if  area < 10:
                self.removeItem(self.temp_item)

                mousePos = event.scenePos()
                if self.pixmap_scene_rect.contains(mousePos):
                    start_item = self.create_startItem("green", mousePos)
                    start_item.setParentItem(self.pixmap_item)
            else:
                self.mouse_start_pos = None
                selected_classes = self.selectClass_Dialog()
                if selected_classes is not None:
                    self.show_boxClass(selected_classes, self.temp_item)

            self.temp_item = None

    def set_pixmap_and_rect(self, pixmap_item: QGraphicsPixmapItem) -> None:
        self.pixmap_item = pixmap_item
        self.pixmap_scene_rect = pixmap_item.mapRectToScene(pixmap_item.boundingRect())

    def add_rect(self, topLeft, bottomRight, classes=None) -> None:
        self.temp_item = AlRectItem(QRectF(topLeft, bottomRight))
        self.temp_item.setParentItem(self.pixmap_item)
        if classes == None:
            classes = self.selectClass_Dialog()
        
        if classes != None:
            self.show_boxClass(classes, self.temp_item)
            
        self.temp_item = None
        
    def calculate_area(self, rect: QRectF) -> float:
        return abs(rect.width() * rect.height())
    
    def create_startItem(self, color: str, pos: QPointF) -> AlStartItem:
        start_item = AlStartItem(color=color)
        start_item.setPos(pos)
        self.show_boxClass(color, start_item)
        return start_item

    def get_rects(self, startPos: QPointF, endPos: QPointF) -> Tuple[QRectF, QRectF]:
        rect = QRectF(startPos, endPos)
        intersect_rect = rect.intersected(self.pixmap_scene_rect)
        return rect, intersect_rect

    def show_boxClass(self, classes: str, item: QGraphicsItem) -> None:
        item.classes = classes

        list_item = QListWidgetItem()
        list_item.setData(Qt.UserRole, item)
        list_item.setText(classes)
        self.class_list.addItem(list_item)

    def selectClass_Dialog(self):
        dialog = CategoryDialog()
        result = dialog.exec_()
        if result == QDialog.Accepted:
            classes = dialog.listWidget.currentItem().text()
            return classes
        elif result == QDialog.Rejected:
            self.removeItem(self.temp_item)
            return None