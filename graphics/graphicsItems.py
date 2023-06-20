from PyQt5.QtWidgets import QGraphicsRectItem, QGraphicsItem, QGraphicsPolygonItem
from PyQt5.QtGui import QBrush, QColor, QPainter, QPen, QKeyEvent, QPolygonF, QPainterPath
from PyQt5.QtCore import Qt, QRectF, QLineF, QPoint
from PyQt5.QtWidgets import QGraphicsSceneHoverEvent, QGraphicsSceneMouseEvent

from utils.general import track_changes


class AlRectItem(QGraphicsRectItem):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setFlags(QGraphicsRectItem.ItemIsMovable | 
                      QGraphicsRectItem.ItemIsSelectable | 
                      QGraphicsItem.ItemSendsGeometryChanges |
                      QGraphicsItem.ItemIsFocusable)
        self.setAcceptHoverEvents(True)
        
        self.classes = None
        self.initial_pos = self.pos()
        self.corner_grabbed = None      # record mouse pressed corner when resizing

    # override
    def paint(self, painter, option, widget=None) -> None:
        if self.isSelected():
            painter.save()
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(QColor(18, 175, 252, 170)))
            painter.drawRect(self.rect())
            painter.restore()
        else:
            painter.setRenderHint(QPainter.SmoothPixmapTransform)
            painter.setPen(QPen(Qt.black, 2))
            painter.setBrush(QBrush(QColor(255, 0, 0, 40)))
            painter.drawRect(self.rect())

            green_pen = QPen(Qt.green, 5)
            for point in self.get_corner_points():
                painter.setPen(green_pen)
                painter.drawPoint(point)
        
        return super().paint(painter, option, widget)
    
    # override
    def keyPressEvent(self, event: QKeyEvent) -> None:
        if self.isSelected():
            step = 1  # stride length
            x, y = self.x(), self.y()

            if event.key() == Qt.Key_Left:
                x -= step
            elif event.key() == Qt.Key_Right:
                x += step
            elif event.key() == Qt.Key_Up:
                y -= step
            elif event.key() == Qt.Key_Down:
                y += step

            self.setPos(x, y)

        return super().keyPressEvent(event)

    # override
    def hoverEnterEvent(self, event: QGraphicsSceneHoverEvent) -> None:
        self.setCursor(Qt.OpenHandCursor)
        return super().hoverEnterEvent(event)
    
    # override
    def hoverMoveEvent(self, event: QGraphicsSceneHoverEvent) -> None:
        mouse_pos = event.scenePos()
        rect = self.boundingRect()
        near_corner = False
        
        positions = [self.mapToScene(rect.topLeft()), 
                     self.mapToScene(rect.topRight()), 
                     self.mapToScene(rect.bottomRight()), 
                     self.mapToScene(rect.bottomLeft())]
        
        for pos in positions:
            if QLineF(mouse_pos, pos).length() <= 10:
                near_corner = True
                self.setCursor(Qt.PointingHandCursor)
                break

        if not near_corner:
            self.setCursor(Qt.OpenHandCursor)


        return super().hoverMoveEvent(event)

    # override
    def hoverLeaveEvent(self, event: QGraphicsSceneHoverEvent) -> None:
        self.unsetCursor()
        return super().hoverLeaveEvent(event)

    # override
    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange and self.parentItem():
            delta = value - self.initial_pos
            new_rect = self.mapRectToScene(self.boundingRect().translated(delta))
            parent_rect = self.mapRectToScene(self.parentItem().boundingRect())

            if not parent_rect.contains(new_rect):  # out of bounds
                dx_left = new_rect.left() - parent_rect.left()
                dx_right = new_rect.right() - parent_rect.right()
                dy_top = new_rect.top() - parent_rect.top()
                dy_bottom = new_rect.bottom() - parent_rect.bottom()

                if dx_left < 0:
                    delta.setX(delta.x() - dx_left)
                elif dx_right > 0:
                    delta.setX(delta.x() - dx_right)
                if dy_top < 0:
                    delta.setY(delta.y() - dy_top)
                elif dy_bottom > 0:
                    delta.setY(delta.y() - dy_bottom)

                return self.initial_pos + delta
            
        return super().itemChange(change, value)
    
    # override
    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        if event.button() == Qt.LeftButton:
            self.setCursor(Qt.ClosedHandCursor)
            mouse_pos = event.pos()
            rect = self.rect()
            mouseRange = 10
            
            if mouse_pos.x() <= rect.left() + mouseRange and mouse_pos.y() <= rect.top() + mouseRange:
                self.corner_grabbed = "topleft"
            elif mouse_pos.x() >= rect.right() - mouseRange and mouse_pos.y() <= rect.top() + mouseRange:
                self.corner_grabbed = "topright"
            elif mouse_pos.x() <= rect.left() + mouseRange and mouse_pos.y() >= rect.bottom() - mouseRange:
                self.corner_grabbed = "bottomleft"
            elif mouse_pos.x() >= rect.right() - mouseRange and mouse_pos.y() >= rect.bottom() - mouseRange:
                self.corner_grabbed = "bottomright"
            else:
                self.corner_grabbed = None
            
            if self.corner_grabbed is not None:
                self.setFlag(QGraphicsItem.ItemIsMovable, False)

        return super().mousePressEvent(event)
    
    # override
    @track_changes
    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        if self.corner_grabbed:
            parent_rect = self.parentItem().boundingRect()
            rect = self.rect()
            mouse_pos = self.mapToScene(event.pos())

            corner_actions = {
                "topleft": rect.setTopLeft,
                "topright": rect.setTopRight,
                "bottomleft": rect.setBottomLeft,
                "bottomright": rect.setBottomRight
            }

            if self.corner_grabbed in corner_actions:
                corner_actions[self.corner_grabbed](event.pos())

            # limit maximum range
            if not parent_rect.contains(self.mapRectToScene(self.boundingRect())):
                if mouse_pos.x() < parent_rect.left():
                    delta = mouse_pos.x() - parent_rect.left()
                    rect.setLeft(rect.left() - delta)
                elif mouse_pos.x() > parent_rect.right():
                    delta = mouse_pos.x() - parent_rect.right()
                    rect.setRight(rect.right() - delta)

                if mouse_pos.y() < parent_rect.top():
                    delta = mouse_pos.y() - parent_rect.top()
                    rect.setTop(rect.top() - delta)
                elif mouse_pos.y() > parent_rect.bottom():
                    delta = mouse_pos.y() - parent_rect.bottom()
                    rect.setBottom(rect.bottom() - delta)

            # limit minimum range
            minSize = 20
            if rect.width() < minSize:
                if self.corner_grabbed == "topleft" or self.corner_grabbed == "bottomleft":
                    rect.setLeft(rect.right() - minSize)
                else:
                    rect.setRight(rect.left() + minSize)

            if rect.height() < minSize:
                if self.corner_grabbed == "topleft" or self.corner_grabbed == "topright":
                    rect.setTop(rect.bottom() - minSize)
                else:
                    rect.setBottom(rect.top() + minSize)

            self.setRect(rect)
        
        return super().mouseMoveEvent(event)
    
    # override
    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        self.corner_grabbed = None
        self.setCursor(Qt.OpenHandCursor)
        self.setFlag(QGraphicsItem.ItemIsMovable, True)

        return super().mouseReleaseEvent(event)

    def get_corner_points(self):
        rect = self.rect()
        return [rect.topLeft(), rect.topRight(), rect.bottomLeft(), rect.bottomRight()]
    

class AlStartItem(QGraphicsPolygonItem):
    def __init__(self, parent=None, color: str="red") -> None:
        super().__init__(parent)
        self.setFlags(QGraphicsPolygonItem.ItemIsMovable | 
                      QGraphicsPolygonItem.ItemIsSelectable |
                      QGraphicsItem.ItemSendsGeometryChanges |
                      QGraphicsItem.ItemIsFocusable)
        self.classes = None
        self.initial_pos = self.pos()

        if color == "red":
            self.color = Qt.red
        elif color == "green":
            self.color = Qt.green
    
    # override
    def paint(self, painter, option, widget=None) -> None:
        painter.setPen(self.color)
        painter.setBrush(self.color)

        points = [
            QPoint(0, -5),
            QPoint(-5, 0),
            QPoint(0, 5),
            QPoint(5, 0),
        ]
        painter.drawPolygon(QPolygonF(points))

        return super().paint(painter, option, widget)
    
    # override
    def keyPressEvent(self, event: QKeyEvent) -> None:
        if self.isSelected():
            step = 1  # stride length
            x, y = self.x(), self.y()

            if event.key() == Qt.Key_Left:
                x -= step
            elif event.key() == Qt.Key_Right:
                x += step
            elif event.key() == Qt.Key_Up:
                y -= step
            elif event.key() == Qt.Key_Down:
                y += step

            self.setPos(x, y)

        return super().keyPressEvent(event)

    # override
    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange and self.parentItem():
            delta = value - self.initial_pos
            new_rect = self.mapRectToScene(self.boundingRect().translated(delta))
            parent_rect = self.mapRectToScene(self.parentItem().boundingRect())

            if not parent_rect.contains(new_rect):
                dx_left = new_rect.left() - parent_rect.left()
                dx_right = new_rect.right() - parent_rect.right()
                dy_top = new_rect.top() - parent_rect.top()
                dy_bottom = new_rect.bottom() - parent_rect.bottom()

                if dx_left < 0:
                    delta.setX(delta.x() - dx_left)
                elif dx_right > 0:
                    delta.setX(delta.x() - dx_right)
                if dy_top < 0:
                    delta.setY(delta.y() - dy_top)
                elif dy_bottom > 0:
                    delta.setY(delta.y() - dy_bottom)

                return self.initial_pos + delta
            
        return super().itemChange(change, value)

    # override
    # mouse selectable range
    def shape(self):    
        extended_rect = self.boundingRect().adjusted(-5, -5, 5, 5)
        path = QPainterPath()
        path.addRect(extended_rect)
        return path
    
    # override
    def boundingRect(self):
        return QRectF(-5, -5, 10, 10)