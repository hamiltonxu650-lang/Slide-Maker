from pathlib import Path

from PyQt6 import QtCore, QtGui, QtWidgets


class RoundedPreview(QtWidgets.QFrame):
    def __init__(self, image_path=None, overlay_color="#120E1A", parent=None):
        super().__init__(parent)
        self.setMinimumSize(176, 168)
        self.setMaximumWidth(176)
        self.setStyleSheet(
            f"background: {overlay_color}; border-radius: 24px; border: 1px solid rgba(255,255,255,0.08);"
        )

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.image_label = QtWidgets.QLabel()
        self.image_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet("background: transparent; border-radius: 24px;")
        layout.addWidget(self.image_label)

        self.setPixmapPath(image_path)

    def setPixmapPath(self, image_path):
        pixmap = None
        if image_path:
            path = Path(image_path)
            if path.exists():
                pixmap = QtGui.QPixmap(str(path))

        if pixmap and not pixmap.isNull():
            scaled = pixmap.scaled(
                176,
                168,
                QtCore.Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                QtCore.Qt.TransformationMode.SmoothTransformation,
            )
            self.image_label.setPixmap(scaled)
            return

        self.image_label.clear()
        self.image_label.setText("预览")
        self.image_label.setStyleSheet(
            "background: transparent; color: rgba(255,255,255,0.7); border-radius: 24px; font-weight: 700;"
        )


class FeatureCard(QtWidgets.QFrame):
    clicked = QtCore.pyqtSignal()

    def __init__(self, title, subtitle, image_path, accent_colors, badge_text, parent=None):
        super().__init__(parent)
        self.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        self.setMinimumHeight(210)
        self.setObjectName("FeatureCardRoot")
        self.setStyleSheet(
            "QFrame#FeatureCardRoot {"
            f"background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {accent_colors[0]}, stop:0.5 {accent_colors[1]}, stop:1 {accent_colors[2]});"
            "border-radius: 28px; border: 1px solid rgba(255,255,255,0.10);"
            "}"
        )

        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(18)

        preview = RoundedPreview(image_path=image_path, overlay_color="#1B1826")
        layout.addWidget(preview)

        content = QtWidgets.QVBoxLayout()
        content.setSpacing(8)
        content.addStretch(1)

        badge = QtWidgets.QLabel(badge_text)
        badge.setStyleSheet(
            "background: rgba(255,255,255,0.18); border: 1px solid rgba(255,255,255,0.24);"
            "border-radius: 11px; padding: 5px 10px; font-size: 12px; font-weight: 700; color: white;"
        )
        content.addWidget(badge, alignment=QtCore.Qt.AlignmentFlag.AlignLeft)

        title_label = QtWidgets.QLabel(title)
        title_label.setStyleSheet("font-size: 34px; font-weight: 900; color: white; background: transparent;")
        content.addWidget(title_label)

        subtitle_label = QtWidgets.QLabel(subtitle)
        subtitle_label.setWordWrap(True)
        subtitle_label.setStyleSheet(
            "font-size: 13px; color: rgba(255,255,255,0.80); background: transparent;"
        )
        content.addWidget(subtitle_label)
        content.addStretch(2)

        arrow = QtWidgets.QLabel("→")
        arrow.setStyleSheet("font-size: 42px; font-weight: 900; color: white; background: transparent;")

        layout.addLayout(content, stretch=1)
        layout.addWidget(arrow, alignment=QtCore.Qt.AlignmentFlag.AlignCenter)

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class PlaceholderCard(QtWidgets.QFrame):
    clicked = QtCore.pyqtSignal(str)

    def __init__(self, title, subtitle, parent=None):
        super().__init__(parent)
        self.title = title
        self.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        self.setMinimumHeight(188)
        self.setObjectName("PlaceholderCardRoot")
        self.setStyleSheet(
            "QFrame#PlaceholderCardRoot {"
            "background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #1D1A28, stop:1 #14121D);"
            "border-radius: 26px; border: 1px solid #2B2840;"
            "}"
        )

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(10)

        thumb = QtWidgets.QFrame()
        thumb.setStyleSheet(
            "background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #2A2737, stop:1 #171621);"
            "border: 1px solid #302C42; border-radius: 22px;"
        )
        thumb_layout = QtWidgets.QVBoxLayout(thumb)
        thumb_layout.setContentsMargins(16, 16, 16, 16)
        thumb_layout.addStretch(1)
        icon = QtWidgets.QLabel(title[:1])
        icon.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        icon.setStyleSheet(
            "background: rgba(255,255,255,0.10); border-radius: 24px; font-size: 26px; font-weight: 900;"
            "min-width: 48px; min-height: 48px; color: white;"
        )
        thumb_layout.addWidget(icon, alignment=QtCore.Qt.AlignmentFlag.AlignLeft)
        thumb_layout.addStretch(1)
        layout.addWidget(thumb, stretch=1)

        title_label = QtWidgets.QLabel(title)
        title_label.setStyleSheet("font-size: 18px; font-weight: 800; color: white; background: transparent;")
        layout.addWidget(title_label)

        subtitle_label = QtWidgets.QLabel(subtitle)
        subtitle_label.setWordWrap(True)
        subtitle_label.setStyleSheet("font-size: 12px; color: #A39BBC; background: transparent;")
        layout.addWidget(subtitle_label)

        status = QtWidgets.QLabel("即将支持")
        status.setStyleSheet(
            "background: rgba(255,255,255,0.06); border-radius: 11px; padding: 6px 10px;"
            "font-size: 12px; color: #F2DCC4; font-weight: 700;"
        )
        layout.addWidget(status, alignment=QtCore.Qt.AlignmentFlag.AlignLeft)

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            self.clicked.emit(self.title)
        super().mousePressEvent(event)

