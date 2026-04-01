from PyQt6 import QtCore, QtWidgets

from services.app_models import APP_BRAND


class Sidebar(QtWidgets.QFrame):
    pageSelected = QtCore.pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Sidebar")
        self.setFixedWidth(228)
        self._buttons = {}

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(18, 20, 18, 20)
        layout.setSpacing(12)

        brand = QtWidgets.QLabel(APP_BRAND)
        brand.setObjectName("SidebarBrand")
        layout.addWidget(brand)

        caption = QtWidgets.QLabel("离线桌面工作台 · PDF / 图片 转 PPTX")
        caption.setObjectName("SidebarCaption")
        caption.setWordWrap(True)
        layout.addWidget(caption)

        layout.addSpacing(14)

        for key, label in (
            ("home", "首页"),
            ("recent", "最近任务"),
            ("settings", "设置"),
            ("about", "关于"),
        ):
            button = QtWidgets.QPushButton(label)
            button.setObjectName("NavButton")
            button.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
            button.clicked.connect(lambda checked=False, page=key: self.select_page(page))
            layout.addWidget(button)
            self._buttons[key] = button

        layout.addStretch(1)

        footer = QtWidgets.QLabel("PDF \u8f6c PPTX \u00b7 \u56fe\u7247\u8f6c PPTX \u00b7 \u66f4\u591a\u5373\u5c06\u63a8\u51fa")
        footer.setObjectName("SidebarCaption")
        footer.setWordWrap(True)
        layout.addWidget(footer)

        self.select_page("home")

    def select_page(self, key):
        for page, button in self._buttons.items():
            button.setProperty("active", page == key)
            button.style().unpolish(button)
            button.style().polish(button)
        self.pageSelected.emit(key)

