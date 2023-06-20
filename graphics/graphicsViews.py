from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QGraphicsPixmapItem, QListWidget
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt

from graphics.graphicsScenes import AlGraphicsScene


class AlGraphicsView(QtWidgets.QGraphicsView):
    def __init__(self, parent=None) -> None:
        super().__init__(parent=parent)
        self.class_list = None
        self.scaled_pixmap = None
        self.scaled_pixmap_item = None
        self.scene_available = False

    def set_class_list(self, class_list: QListWidget) -> None:
        self.class_list = class_list

    def set_pixmap(self, pixmap: QPixmap) -> None:
        if not self.scene_available:
            self.scene_available = True
            self.al_scene = AlGraphicsScene(class_list=self.class_list)
            self.setScene(self.al_scene)

        
        self.al_scene.clear()       # initial data
        self.class_list.clear()     # initial data
        
        self.scaled_pixmap = pixmap.scaled(self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.scaled_pixmap_item = QGraphicsPixmapItem(self.scaled_pixmap)
        self.al_scene.addItem(self.scaled_pixmap_item)
        self.al_scene.setSceneRect(self.scaled_pixmap_item.boundingRect())
        self.al_scene.set_pixmap_and_rect(self.scaled_pixmap_item)

    def get_scaled_pixmap(self) -> QPixmap:
        return self.scaled_pixmap