from PyQt6 import QtCore, QtGui, QtWidgets

from services.app_models import APP_BRAND
from services.runtime_env import find_app_icon


class CustomTitleBar(QtWidgets.QFrame):
    def __init__(self, window, parent=None):
        super().__init__(parent)
        self._window = window
        self._drag_offset = None
        self.setObjectName("TitleBar")
        self.setFixedHeight(56)

        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(14, 8, 8, 8)
        layout.setSpacing(12)

        logo = QtWidgets.QLabel()
        logo.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        logo.setFixedSize(32, 32)
        icon_path = find_app_icon()
        if icon_path:
            pixmap = QtGui.QPixmap(str(icon_path)).scaled(
                32,
                32,
                QtCore.Qt.AspectRatioMode.KeepAspectRatio,
                QtCore.Qt.TransformationMode.SmoothTransformation,
            )
            logo.setPixmap(pixmap)
        else:
            logo.setText("S")
            logo.setStyleSheet(
                "background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #FF4F6A, stop:1 #FFB147);"
                "border-radius: 10px; color: white; font-size: 18px; font-weight: 900;"
            )
        layout.addWidget(logo)

        text_layout = QtWidgets.QVBoxLayout()
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(0)

        brand = QtWidgets.QLabel(APP_BRAND)
        brand.setObjectName("TitleBrand")
        text_layout.addWidget(brand)

        meta = QtWidgets.QLabel("各种格式转 PPTX 的离线桌面工作台")
        meta.setObjectName("TitleMeta")
        text_layout.addWidget(meta)
        layout.addLayout(text_layout)
        layout.addStretch(1)

        self.min_button = self._create_button(
            self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_TitleBarMinButton),
            lambda: self._window.showMinimized(),
        )
        layout.addWidget(self.min_button)

        self.max_button = self._create_button(
            self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_TitleBarMaxButton),
            self._toggle_maximize,
        )
        layout.addWidget(self.max_button)

        self.close_button = self._create_button(
            self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_TitleBarCloseButton),
            self._window.close,
            close=True,
        )
        layout.addWidget(self.close_button)

    def _create_button(self, icon, callback, close=False):
        button = QtWidgets.QPushButton()
        button.setObjectName("CloseButton" if close else "WindowButton")
        button.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        button.setFixedSize(46, 32)
        button.setIcon(icon)
        button.setIconSize(QtCore.QSize(12, 12))
        button.clicked.connect(callback)
        return button

    def update_window_state(self, maximized):
        icon_type = (
            QtWidgets.QStyle.StandardPixmap.SP_TitleBarNormalButton
            if maximized
            else QtWidgets.QStyle.StandardPixmap.SP_TitleBarMaxButton
        )
        self.max_button.setIcon(self.style().standardIcon(icon_type))

    def _toggle_maximize(self):
        if self._window.isMaximized():
            self._window.showNormal()
        else:
            self._window.showMaximized()

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            child = self.childAt(event.position().toPoint())
            if isinstance(child, QtWidgets.QPushButton):
                super().mousePressEvent(event)
                return
            window_handle = self._window.windowHandle()
            if window_handle is not None and hasattr(window_handle, "startSystemMove"):
                if window_handle.startSystemMove():
                    event.accept()
                    return
            self._drag_offset = event.globalPosition().toPoint() - self._window.frameGeometry().topLeft()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() & QtCore.Qt.MouseButton.LeftButton and self._drag_offset and not self._window.isMaximized():
            self._window.move(event.globalPosition().toPoint() - self._drag_offset)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._drag_offset = None
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event):
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            self._toggle_maximize()
        super().mouseDoubleClickEvent(event)
