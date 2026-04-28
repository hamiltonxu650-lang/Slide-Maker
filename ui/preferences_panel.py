from __future__ import annotations

from PyQt6 import QtCore, QtGui, QtWidgets

from services.app_models import (
    PREFERENCE_CLARITY,
    PREFERENCE_CLEANUP,
    PREFERENCE_LAYOUT,
    PREFERENCE_SPEED,
    TaskPreferences,
)
from ui.icons import svg_icon


UI_PREFERENCE_CHOICES = (
    PREFERENCE_CLARITY,
    PREFERENCE_CLEANUP,
    PREFERENCE_SPEED,
)

PREFERENCE_TEXT = {
    PREFERENCE_LAYOUT: ("默认", "尽量保持原图中的排版位置和层级。"),
    PREFERENCE_CLARITY: ("默认", "优先文字清晰"),
    PREFERENCE_CLEANUP: ("优先背景干净", "加强去字和背景修复，减少残影。"),
    PREFERENCE_SPEED: ("优先转换速度", "快速生成首版 PPTX，适合批量预览。"),
}

PREFERENCE_ICONS = {
    PREFERENCE_CLARITY: "type",
    PREFERENCE_CLEANUP: "eraser",
    PREFERENCE_SPEED: "zap",
}


class PreferenceCard(QtWidgets.QFrame):
    clicked = QtCore.pyqtSignal(str)

    def __init__(self, key, title, desc, parent=None):
        super().__init__(parent)
        self.key = key
        self.setObjectName("PreferenceChoice")
        self.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        self.setMinimumHeight(104)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(6)
        layout.addStretch(1)

        self.icon_label = QtWidgets.QLabel()
        self.icon_label.setObjectName("PreferenceChoiceIcon")
        self.icon_label.setFixedSize(30, 30)
        self.icon_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.icon_label.setPixmap(svg_icon(PREFERENCE_ICONS.get(key, "type"), "#17191F", 26).pixmap(26, 26))
        layout.addWidget(self.icon_label, alignment=QtCore.Qt.AlignmentFlag.AlignHCenter)

        self.title_label = QtWidgets.QLabel(title)
        self.title_label.setObjectName("PreferenceChoiceTitle")
        self.title_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.title_label.setWordWrap(True)
        layout.addWidget(self.title_label)

        self.desc_label = QtWidgets.QLabel(desc)
        self.desc_label.setObjectName("PreferenceHint")
        self.desc_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.desc_label.setWordWrap(True)
        layout.addWidget(self.desc_label)

        layout.addStretch(1)

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            self.clicked.emit(self.key)
        super().mousePressEvent(event)

    def set_active(self, active):
        self.setProperty("active", active)
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()


class PreferencePanel(QtWidgets.QFrame):
    preferencesChanged = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("PreferencePanel")
        self._cards = {}
        self._selected = PREFERENCE_CLARITY

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(22, 22, 22, 22)
        layout.setSpacing(14)

        title = QtWidgets.QLabel("转换偏好")
        title.setObjectName("StatusTitle")
        layout.addWidget(title)

        caption = QtWidgets.QLabel("选择一个生成模式，Slide Maker 会把对应偏好应用到本地转换流程。")
        caption.setObjectName("StatusCaption")
        caption.setWordWrap(True)
        layout.addWidget(caption)

        segment_bar = QtWidgets.QFrame()
        segment_bar.setObjectName("PreferenceSegmentBar")
        segment_layout = QtWidgets.QHBoxLayout(segment_bar)
        segment_layout.setContentsMargins(6, 6, 6, 6)
        segment_layout.setSpacing(6)

        for index, key in enumerate(UI_PREFERENCE_CHOICES):
            title_text, desc = PREFERENCE_TEXT[key]
            card = PreferenceCard(key, title_text, desc)
            card.clicked.connect(self._select_choice)
            self._cards[key] = card
            segment_layout.addWidget(card, stretch=1)

        layout.addWidget(segment_bar)

        note_title = QtWidgets.QLabel("补充备注")
        note_title.setObjectName("MutedLabel")
        layout.addWidget(note_title)

        self.note_edit = QtWidgets.QPlainTextEdit()
        self.note_edit.setObjectName("PreferenceNoteEdit")
        self.note_edit.setPlaceholderText("例如：希望文字更清晰一点，背景残影少一些。")
        self.note_edit.setMaximumHeight(90)
        self.note_edit.textChanged.connect(self.preferencesChanged.emit)
        layout.addWidget(self.note_edit)

        self.keyword_hint = QtWidgets.QLabel(
            "备注只会做本地关键词映射，例如“清晰、背景、速度”等词。"
        )
        self.keyword_hint.setObjectName("PreferenceHint")
        self.keyword_hint.setWordWrap(True)
        layout.addWidget(self.keyword_hint)

        self.set_preferences(TaskPreferences())

    def get_preferences(self) -> TaskPreferences:
        return TaskPreferences(focus=self._selected, note=self.note_edit.toPlainText().strip()).with_mapped_tags()

    def set_preferences(self, preferences: TaskPreferences) -> None:
        preferences = TaskPreferences.from_dict(preferences.to_dict() if isinstance(preferences, TaskPreferences) else preferences)
        focus = preferences.focus if preferences.focus in self._cards else PREFERENCE_CLARITY
        self._select_choice(focus, emit=False)
        self.note_edit.setPlainText(preferences.note)

    def _select_choice(self, key, emit=True):
        self._selected = key if key in self._cards else PREFERENCE_CLARITY
        for card_key, card in self._cards.items():
            card.set_active(card_key == self._selected)
        if emit:
            self.preferencesChanged.emit()
