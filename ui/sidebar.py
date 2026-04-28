from PyQt6 import QtCore, QtGui, QtWidgets

from services.app_models import APP_BRAND
from services.runtime_env import find_app_display_icon
from ui.icons import sharp_pixmap, svg_icon


NAV_ITEMS = (
    ("home", "home", "Home"),
    ("recent", "clock", "Recent"),
    ("settings", "settings", "Settings"),
    ("about", "info", "About"),
)


class Sidebar(QtWidgets.QFrame):
    pageSelected = QtCore.pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Sidebar")
        self.setFixedWidth(92)
        self._buttons = {}

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(12, 18, 12, 18)
        layout.setSpacing(18)

        logo = QtWidgets.QLabel()
        logo.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        logo.setFixedSize(46, 46)
        icon_path = find_app_display_icon()
        if icon_path:
            logo.setPixmap(sharp_pixmap(icon_path, 42))
        else:
            logo.setText("S")
            logo.setObjectName("SidebarBrand")
        layout.addWidget(logo, alignment=QtCore.Qt.AlignmentFlag.AlignHCenter)

        dock = QtWidgets.QFrame()
        dock.setObjectName("RailDock")
        dock_layout = QtWidgets.QVBoxLayout(dock)
        dock_layout.setContentsMargins(10, 16, 10, 16)
        dock_layout.setSpacing(18)
        layout.addWidget(dock, alignment=QtCore.Qt.AlignmentFlag.AlignHCenter)

        for key, icon_name, tooltip in NAV_ITEMS:
            button = QtWidgets.QPushButton()
            button.setObjectName("RailButton")
            button.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
            button.setToolTip(tooltip)
            button.setFixedSize(44, 44)
            button.setIconSize(QtCore.QSize(21, 21))
            button.setProperty("iconName", icon_name)
            button.clicked.connect(lambda checked=False, page=key: self.select_page(page))
            dock_layout.addWidget(button, alignment=QtCore.Qt.AlignmentFlag.AlignHCenter)
            self._buttons[key] = button

        layout.addStretch(1)

        self.select_page("home")

    def select_page(self, key):
        for page, button in self._buttons.items():
            active = page == key
            icon_color = "#FFE75F" if active else "#383D48"
            button.setProperty("active", active)
            button.setIcon(svg_icon(button.property("iconName"), icon_color, 22))
            button.style().unpolish(button)
            button.style().polish(button)
        self.pageSelected.emit(key)
