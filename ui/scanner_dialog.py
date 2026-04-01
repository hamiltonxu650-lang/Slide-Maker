from PyQt6 import QtCore, QtGui, QtWidgets
import cv2
import numpy as np


def _cv2_to_qpixmap(cv_img: np.ndarray) -> QtGui.QPixmap:
    """Convert an OpenCV BGR image to QPixmap, works with any format cv2 can read."""
    rgb = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
    h, w, ch = rgb.shape
    bytes_per_line = ch * w
    q_img = QtGui.QImage(rgb.data, w, h, bytes_per_line, QtGui.QImage.Format.Format_RGB888)
    return QtGui.QPixmap.fromImage(q_img.copy())  # .copy() ensures data ownership


class CornerHandle(QtWidgets.QGraphicsEllipseItem):
    def __init__(self, x, y, radius, index, parent=None):
        super().__init__(-radius, -radius, 2 * radius, 2 * radius, parent)
        self.setPos(x, y)
        self.radius = radius
        self.index = index
        self.setBrush(QtGui.QBrush(QtGui.QColor(0, 150, 255, 180)))
        self.setPen(QtGui.QPen(QtGui.QColor(255, 255, 255), 2))
        self.setFlag(QtWidgets.QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QtWidgets.QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)
        self.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self.setZValue(10)

    def itemChange(self, change, value):
        if change == QtWidgets.QGraphicsItem.GraphicsItemChange.ItemPositionChange:
            if self.scene():
                self.scene().update_polygon()
        return super().itemChange(change, value)


class ScannerScene(QtWidgets.QGraphicsScene):
    def __init__(self, cv_img: np.ndarray, initial_pts=None, parent=None):
        super().__init__(parent)
        self.pixmap = _cv2_to_qpixmap(cv_img)
        self.addPixmap(self.pixmap)

        self.polygon_item = QtWidgets.QGraphicsPolygonItem()
        self.polygon_item.setPen(QtGui.QPen(QtGui.QColor(0, 150, 255), 3))
        self.polygon_item.setBrush(QtGui.QBrush(QtGui.QColor(0, 150, 255, 40)))
        self.addItem(self.polygon_item)

        self.handles = []
        if initial_pts is None:
            w = self.pixmap.width()
            h = self.pixmap.height()
            padding_x = w * 0.1
            padding_y = h * 0.1
            initial_pts = [
                [padding_x, padding_y],
                [w - padding_x, padding_y],
                [w - padding_x, h - padding_y],
                [padding_x, h - padding_y],
            ]

        # radius scales with image size to make it easy to grab
        base_radius = max(15, min(self.pixmap.width(), self.pixmap.height()) * 0.02)

        for i, pt in enumerate(initial_pts):
            handle = CornerHandle(pt[0], pt[1], base_radius, i)
            self.addItem(handle)
            self.handles.append(handle)

        self.update_polygon()

    def update_polygon(self):
        poly = QtGui.QPolygonF()
        for handle in self.handles:
            poly.append(handle.pos())
        self.polygon_item.setPolygon(poly)

    def get_points(self) -> np.ndarray:
        return np.array([[h.pos().x(), h.pos().y()] for h in self.handles], dtype=np.float32)


class ScannerDialog(QtWidgets.QDialog):
    """
    Accepts a cv2 BGR image (np.ndarray) instead of a file path.
    This ensures any format loadable by cv2 (including HEIC via sips conversion) works.
    """
    def __init__(self, cv_img: np.ndarray, initial_pts=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("手动调整裁边 - Slide Maker")
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.WindowType.WindowStaysOnTopHint)
        self.setWindowModality(QtCore.Qt.WindowModality.ApplicationModal)
        self.setMinimumSize(800, 600)
        self.resize(1000, 800)

        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.main_layout.setContentsMargins(12, 12, 12, 12)

        self.view = QtWidgets.QGraphicsView()
        self.scene = ScannerScene(cv_img, initial_pts, self)
        self.view.setScene(self.scene)
        self.view.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        self.view.setDragMode(QtWidgets.QGraphicsView.DragMode.ScrollHandDrag)
        self.view.setStyleSheet("background: #1e1e1e; border: 1px solid #333;")

        self.main_layout.addWidget(self.view, stretch=1)

        btn_layout = QtWidgets.QHBoxLayout()
        self.info_label = QtWidgets.QLabel("拖动四个控制点，使其贴合文档真实边缘，系统将利用透视变换裁正。")
        self.info_label.setStyleSheet("color: #ccc; font-size: 14px;")
        btn_layout.addWidget(self.info_label)

        btn_layout.addStretch(1)

        self.skip_btn = QtWidgets.QPushButton("跳过裁正")
        self.skip_btn.setMinimumHeight(35)
        self.skip_btn.setMinimumWidth(120)
        self.skip_btn.clicked.connect(self.reject)

        self.confirm_btn = QtWidgets.QPushButton("确认裁剪")
        self.confirm_btn.setMinimumHeight(35)
        self.confirm_btn.setMinimumWidth(120)
        self.confirm_btn.setStyleSheet("background-color: #0078D7; color: white; font-weight: bold;")
        self.confirm_btn.clicked.connect(self.accept)

        btn_layout.addWidget(self.skip_btn)
        btn_layout.addWidget(self.confirm_btn)
        self.main_layout.addLayout(btn_layout)

    def showEvent(self, event):
        super().showEvent(event)
        self.view.fitInView(self.scene.itemsBoundingRect(), QtCore.Qt.AspectRatioMode.KeepAspectRatio)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.view.fitInView(self.scene.itemsBoundingRect(), QtCore.Qt.AspectRatioMode.KeepAspectRatio)

    def get_points(self) -> np.ndarray:
        return self.scene.get_points()
