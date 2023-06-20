from typing import Tuple, List
from pathlib import Path
from collections import OrderedDict
from lxml import etree as ET
import json

from PyQt5.QtCore import QPointF, Qt, QSize, QPoint
from PyQt5.QtWidgets import QFileDialog, QGraphicsRectItem, QListWidget
from PyQt5.QtGui import QTransform

from utils.classSelectionDialog import CategoryDialog

class Data():
    coco_images = OrderedDict()
    coco_images_info = []
    coco_annotations_info = []
    coco_categories_info = []

    is_modified = False


def track_changes(func):
    def wrapper(*args, **kwargs):
        Data.is_modified = True
        return func(*args, **kwargs)
    return wrapper

def reorder(annotations: list) -> None:
    for idx, annot in enumerate(annotations):
        annot["id"] = idx

def get_key_by_value(dictionary: dict, value):
    for key, val in dictionary.items():
        if val == value:
            return key
    return None

def to_orig_pos(scenePos: QPointF, scaled_size: QSize, ori_size: QSize) -> Tuple[int, int]:
    scale_x = ori_size.width() / scaled_size.width()
    scale_y = ori_size.height() / scaled_size.height()

    transform = QTransform().scale(scale_x, scale_y)
    o_pos = transform.map(scenePos.toPoint())

    return o_pos.x(), o_pos.y()

def to_scaled_pos(ori_x: int, ori_y: int, scaled_size: QSize, ori_size: QSize) -> QPoint:
    scale_x = scaled_size.width() / ori_size.width()
    scale_y = scaled_size.height() / ori_size.height()

    transform = QTransform().scale(scale_x, scale_y)
    p_pos = transform.map(QPoint(ori_x, ori_y))

    return p_pos

def parse_yolo(file_path: str, scaled_h: int, scaled_w: int) -> List[Tuple[QPointF, QPointF, str]]:
    boxes = []
    with open(file_path, "r") as f:
        lines = f.readlines()
        for line in lines:
            box = line.split()
            if len(box) == 5:
                classes_idx, x, y, w, h = box[0], box[1], box[2], box[3], box[4]
                try:
                    classes = CategoryDialog.classes[int(classes_idx)]
                    x1, y1, x2, y2 = yolo_to_bbox(float(x), float(y), float(w), float(h), scaled_h, scaled_w)
                    boxes.append((classes, QPointF(x1, y1), QPointF(x2, y2)))
                except IndexError:
                    print(f"The categories of \"{file_path}\" and \"classes.txt\" are inconsistent.")
                    return boxes
                
    return boxes

def parse_xml(file_path: str, scaled_size: QSize, ori_size: QSize) -> List[Tuple[QPointF, QPointF, str]]:
    bboxes = []
    classes, x1, y1, x2, y2 = None, None, None, None, None

    tree = ET.parse(file_path)
    root = tree.getroot()
    for element in root.iter():
        if element.tag == "name":
            classes = element.text
        elif element.tag == "xmin":
            x1 = int(element.text)
        elif element.tag == "ymin":
            y1 = int(element.text)
        elif element.tag == "xmax":
            x2 = int(element.text)
        elif element.tag == "ymax":
            y2 = int(element.text)
        
        if all(val is not None for val in [classes, x1, y1, x2, y2]):
            scaled_topLeft = to_scaled_pos(x1, y1, scaled_size, ori_size)
            scaled_bottomRight = to_scaled_pos(x2, y2, scaled_size, ori_size)
            bboxes.append((classes, scaled_topLeft, scaled_bottomRight))
            classes, x1, y1, x2, y2 = None, None, None, None, None

    return bboxes

def parse_coco(file_path: str, file_name: str, classes_mapping: dict, scaled_size: QSize, ori_size: QSize) -> List[Tuple[QPointF, QPointF, str]]:
    image_id = -1
    bboxes = []

    with open(file_path, "r") as file:
        data = json.load(file)

    for img in data["images"]:
        if img["file_name"] == file_name:
            image_id = img["id"]
            break
    
    for annot in data["annotations"]:
        if annot["image_id"] == image_id:
            classes = get_key_by_value(classes_mapping, annot["category_id"])
            if classes is None:
                print(f"The categories of \"{file_path}\" and \"classes.txt\" are inconsistent.")
                return bboxes
            else:
                bbox = annot["bbox"]
                x1, y1, w, h = int(bbox[0]), int(bbox[1]), int(bbox[2]), int(bbox[3])

                p_topLeft = to_scaled_pos(x1, y1, scaled_size, ori_size)
                p_bottomRight = to_scaled_pos(x1+w, y1+h, scaled_size, ori_size)
                bboxes.append((classes, p_topLeft, p_bottomRight))
    
    return bboxes

def yolo_to_bbox(x: float, y: float, w: float, h: float, scaled_h: int, scaled_w: int) -> Tuple[float, float, float, float]:
    x1, y1 = (x-w/2)*scaled_w, (y-h/2)*scaled_h
    x2, y2 = (x+w/2)*scaled_w, (y+h/2)*scaled_h

    return x1, y1, x2, y2

def box_to_yolo(img_h: int, img_w: int, box: QGraphicsRectItem) -> Tuple[float, float, float, float]:
    center_x = box.boundingRect().center().x()
    center_y = box.boundingRect().center().y()

    x = center_x / img_w
    y = center_y / img_h
    width = box.boundingRect().width() / img_w
    height = box.boundingRect().height() / img_h

    return x, y, width, height

def box_to_pascal(classes: str, box: QGraphicsRectItem, ori_size: QSize, scaled_size: QSize) -> dict:
    xmin, ymin = to_orig_pos(box.boundingRect().topLeft(), scaled_size, ori_size)
    xmax, ymax = to_orig_pos(box.boundingRect().bottomRight(), scaled_size, ori_size)
    
    xmin, ymin, xmax, ymax = [max(0, val) for val in [xmin, ymin, xmax, ymax]]
    obj = {
        "name": classes,
        "pose": "Unspecified",
        "truncated": "0",
        "difficult": "0",
        "xmin": xmin,
        "ymin": ymin,
        "xmax": xmax,
        "ymax": ymax,
    }

    return obj

def box_to_coco(file_name: Path, box_labels: QListWidget, classes_mapping: dict, scaled_size: QSize, ori_size: QSize) -> None:
    coco_images(file_name, ori_size)
    coco_annotations(file_name, box_labels, classes_mapping, scaled_size, ori_size)
    coco_categories(classes_mapping)

def coco_images(file_name: Path, ori_size: QSize):
    Data.coco_images[file_name] = None
    image_id = list(Data.coco_images.keys()).index(file_name)
    width = ori_size.width()
    height = ori_size.height()

    if image_id not in [img["id"] for img in Data.coco_images_info]:
        Data.coco_images_info.append({
            "id": image_id,
            "file_name": file_name, 
            "width": width, 
            "height": height
        })

def coco_annotations(file_name: Path, box_labels: QListWidget, classes_mapping: dict, scaled_size: QSize, ori_size: QSize) -> None:
    iscrowd = 0
    ignore = 0
    image_id = list(Data.coco_images).index(file_name)
    segmentation = []
    temp_annotations = [annot for annot in Data.coco_annotations_info if annot["image_id"] != image_id]

    for row in range(box_labels.count()):
        item = box_labels.item(row)
        classes = item.text()
        
        if classes in classes_mapping:
            box = item.data(Qt.UserRole)
            
            x1, y1 = to_orig_pos(box.boundingRect().topLeft(), scaled_size, ori_size)
            x2, y2 = to_orig_pos(box.boundingRect().bottomRight(), scaled_size, ori_size)
            x1, y1, x2, y2 = [max(0, val) for val in [x1, y1, x2, y2]]
            bbox = [float(x1), float(y1), float(x2-x1), float(y2-y1)]

            area = float(x2-x1) * float(y2-y1)
            category_id = classes_mapping[classes]
            id = len(Data.coco_annotations_info)               
            
            temp_annotations.append({
                "iscrowd": iscrowd, 
                "ignore": ignore, 
                "image_id": image_id, 
                "bbox": bbox, 
                "area": area, 
                "segmentation": segmentation, 
                "category_id": category_id, 
                "id": id
            })
    Data.coco_annotations_info = temp_annotations
    reorder(Data.coco_annotations_info)

def coco_categories(classes_mapping: dict) -> None:
    Data.coco_categories_info = []    # initial

    supercategory = "none"
    for classes, id in classes_mapping.items():
        Data.coco_categories_info.append({
            "supercategory": supercategory, 
            "id": id, 
            "name": classes
    })

def write_yolo_file(boxes: list, save_path: str) -> None:
    with open(save_path, "w") as f:
        for box in boxes:
            classes_idx, x, y, w, h = box
            f.write(f"{classes_idx} {x:.6f} {y:.6f} {w:.6f} {h:.6f}\n")
    
    print(f"Annotation to {save_path}")

def write_pascal_file(folder: str, filename: str, file_path: str, width: str, height: str, objects: list, save_path: str) -> None:
    root = ET.Element('annotation')

    folder_elem = ET.SubElement(root, 'folder')
    folder_elem.text = folder

    folder_elem = ET.SubElement(root, 'filename')
    folder_elem.text = filename

    path_elem = ET.SubElement(root, 'path')
    path_elem.text = file_path

    source_elem = ET.SubElement(root, 'source')
    database_elem = ET.SubElement(source_elem, 'database')
    database_elem.text = "Unknown"

    size_elem = ET.SubElement(root, 'size')
    width_elem = ET.SubElement(size_elem, 'width')
    width_elem.text = str(width)
    height_elem = ET.SubElement(size_elem, 'height')
    height_elem.text = str(height)
    depth_elem = ET.SubElement(size_elem, 'depth')
    depth_elem.text = "3"

    segmented_elem = ET.SubElement(root, 'segmented')
    segmented_elem.text = "0"

    for obj_info in objects:
        object_elem = ET.SubElement(root, 'object')
        name_elem = ET.SubElement(object_elem, 'name')
        name_elem.text = obj_info['name']

        pose_elem = ET.SubElement(object_elem, 'pose')
        pose_elem.text = obj_info['pose']

        truncated_elem = ET.SubElement(object_elem, 'truncated')
        truncated_elem.text = obj_info['truncated']

        difficult_elem = ET.SubElement(object_elem, 'difficult')
        difficult_elem.text = obj_info['difficult']

        bndbox_elem = ET.SubElement(object_elem, 'bndbox')
        xmin_elem = ET.SubElement(bndbox_elem, 'xmin')
        xmin_elem.text = str(obj_info['xmin'])
        ymin_elem = ET.SubElement(bndbox_elem, 'ymin')
        ymin_elem.text = str(obj_info['ymin'])
        xmax_elem = ET.SubElement(bndbox_elem, 'xmax')
        xmax_elem.text = str(obj_info['xmax'])
        ymax_elem = ET.SubElement(bndbox_elem, 'ymax')
        ymax_elem.text = str(obj_info['ymax'])

    xml_tree = ET.ElementTree(root)

    xml_tree.write(save_path, encoding='utf-8', xml_declaration=False, pretty_print=True)
    print(f"Annotation to {save_path}")

def write_coco_file(data: dict, save_path: str) -> None:
    with open(save_path, "w") as file:
        json.dump(data, file, indent=4)

    print(f"Annotation to {save_path}")

def save_yolo_format(file_path: Path, box_labels: QListWidget, classes_mapping: dict, scaled_size: QSize, options) -> None:
    bboxes = []
    for row in range(box_labels.count()):
        item = box_labels.item(row)
        classes = item.text()
        if classes in classes_mapping:
            box = item.data(Qt.UserRole)
            scaled_h, scaled_w = scaled_size.height(), scaled_size.width()

            x, y, w, h = box_to_yolo(scaled_h, scaled_w, box)
            bboxes.append((classes_mapping[classes], x, y, w, h))
    
    save_path, _ = QFileDialog.getSaveFileName(None, "Save File", str(file_path.with_suffix(".txt")), "Text Files (*.txt)", options=options)
    if save_path:
        write_yolo_file(bboxes, save_path)

def save_pascal_format(file_path: Path, box_labels: QListWidget, classes_mapping: dict, scaled_size: QSize, ori_size: QSize, options) -> None:
    folder = file_path.parent.name
    file_name = file_path.name
    width = ori_size.width()
    height = ori_size.height()

    objects = []
    for row in range(box_labels.count()):
        item = box_labels.item(row)
        classes = item.text()
        if classes in classes_mapping:
            box = item.data(Qt.UserRole)
            obj = box_to_pascal(classes, box, ori_size, scaled_size)
            objects.append(obj)

    save_path, _ = QFileDialog.getSaveFileName(None, "Save File", str(file_path.with_suffix(".xml")), "XML Files (*.xml)", options=options)
    if save_path:
        write_pascal_file(folder, file_name, str(file_path), width, height, objects, save_path)

def save_coco_format(file_path: Path, box_labels: QListWidget, classes_mapping: dict, scaled_size: QSize, ori_size: QSize, options) -> None:
    file_name = file_path.name
    box_to_coco(file_name, box_labels, classes_mapping, scaled_size, ori_size)
    data = {
        "images": Data.coco_images_info,
        "annotations": Data.coco_annotations_info,
        "categories": Data.coco_categories_info
    }

    save_path, _ = QFileDialog.getSaveFileName(None, "Save File", str(file_path.parent / "annotations.json"), "JSON Files (*.json)", options=options)
    if save_path:
        write_coco_file(data, save_path)