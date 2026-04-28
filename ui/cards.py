from pathlib import Path

from PyQt6 import QtCore, QtGui, QtWidgets

from ui.icons import svg_icon, svg_pixmap

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
        self.setMinimumHeight(220)
        self.setObjectName("FeatureCardRoot")
        self.setStyleSheet(
            "QFrame#FeatureCardRoot {"
            f"background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {accent_colors[0]}, stop:0.55 {accent_colors[1]}, stop:1 {accent_colors[2]});"
            "border-radius: 28px; border: 1px solid rgba(255,255,255,0.70);"
            "}"
        )

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 20)
        layout.setSpacing(10)

        kicker = QtWidgets.QLabel(badge_text)
        kicker.setStyleSheet(
            "background: rgba(255,255,255,0.58); border-radius: 13px; padding: 5px 11px;"
            "font-size: 12px; font-weight: 800; color: rgba(25,30,42,0.66);"
        )
        layout.addWidget(kicker, alignment=QtCore.Qt.AlignmentFlag.AlignLeft)

        title_label = QtWidgets.QLabel(title)
        title_label.setStyleSheet("font-size: 25px; font-weight: 900; color: #17191F; background: transparent;")
        layout.addWidget(title_label)

        subtitle_label = QtWidgets.QLabel(subtitle)
        subtitle_label.setWordWrap(True)
        subtitle_label.setStyleSheet(
            "font-size: 14px; color: #485160; background: transparent; line-height: 150%;"
        )
        layout.addWidget(subtitle_label)

        detail_text = "适合课件、报告、扫描 PDF" if "PDF" in title else "支持 PNG / JPG / JPEG，适合单页设计稿"
        detail_label = QtWidgets.QLabel(detail_text)
        detail_label.setWordWrap(True)
        detail_label.setStyleSheet("font-size: 12px; color: rgba(38,47,66,0.62); background: transparent;")
        layout.addWidget(detail_label)

        layout.addStretch(1)

        tag_row = QtWidgets.QHBoxLayout()
        tag_row.setSpacing(8)
        tag_specs = (
            ("layers", "高保真"),
            ("scan-line", "OCR"),
            ("sparkles", "净化"),
        )
        for icon_name, tag in tag_specs:
            tag_pill = QtWidgets.QFrame()
            tag_pill.setObjectName("FeatureTagPill")
            tag_pill.setStyleSheet(
                "QFrame#FeatureTagPill {"
                "background: rgba(255,255,255,0.72); border-radius: 14px;"
                "}"
            )
            tag_layout = QtWidgets.QHBoxLayout(tag_pill)
            tag_layout.setContentsMargins(10, 7, 11, 7)
            tag_layout.setSpacing(5)

            icon = QtWidgets.QLabel()
            icon.setFixedSize(15, 15)
            icon.setPixmap(svg_pixmap(icon_name, "#2F78FF", 15, 2.2))
            tag_layout.addWidget(icon)

            label = QtWidgets.QLabel(tag)
            label.setStyleSheet(
                "background: transparent; font-size: 12px; font-weight: 800; color: #17191F;"
            )
            tag_layout.addWidget(label)
            tag_row.addWidget(tag_pill)
        tag_row.addStretch(1)
        layout.addLayout(tag_row)

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class PlaceholderCard(QtWidgets.QFrame):
    clicked = QtCore.pyqtSignal(str)

    def __init__(self, title, subtitle, icon_name="file-type", parent=None):
        super().__init__(parent)
        self.title = title
        self.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        self.setMinimumHeight(108)
        self.setObjectName("PlaceholderCardRoot")
        self.setStyleSheet(
            "QFrame#PlaceholderCardRoot {"
            "background: rgba(255,255,255,0.88);"
            "border-radius: 22px; border: 1px solid rgba(255,255,255,0.72);"
            "}"
        )

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(6)

        icon = QtWidgets.QLabel()
        icon.setFixedSize(24, 24)
        icon.setPixmap(svg_pixmap(icon_name, "#2F78FF", 22))
        layout.addWidget(icon)

        title_label = QtWidgets.QLabel(title)
        title_label.setStyleSheet("font-size: 14px; font-weight: 900; color: #17191F; background: transparent;")
        layout.addWidget(title_label)

        subtitle_label = QtWidgets.QLabel(subtitle)
        subtitle_label.setWordWrap(True)
        subtitle_label.setStyleSheet("font-size: 12px; color: #7C828D; background: transparent;")
        layout.addWidget(subtitle_label)
        layout.addStretch(1)

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            self.clicked.emit(self.title)
        super().mousePressEvent(event)
