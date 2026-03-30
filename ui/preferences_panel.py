from __future__ import annotations

from PyQt6 import QtCore, QtWidgets

from services.app_models import (
    PREFERENCE_CHOICES,
    PREFERENCE_CLARITY,
    PREFERENCE_CLEANUP,
    PREFERENCE_LAYOUT,
    PREFERENCE_SPEED,
    TaskPreferences,
)


PREFERENCE_TEXT = {
    PREFERENCE_LAYOUT: ("默认", "尽量保持原图中的排版位置和层级。"),
    PREFERENCE_CLARITY: ("优先文字清晰", "提高文字可读性，适合文字较多的页面。"),
    PREFERENCE_CLEANUP: ("优先背景干净", "更强调去字和背景修复效果。"),
    PREFERENCE_SPEED: ("优先转换速度", "牺牲部分精细度，优先更快完成转换。"),
}


class PreferencePanel(QtWidgets.QFrame):
    preferencesChanged = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("PreferencePanel")
        self._buttons = {}

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(22, 22, 22, 22)
        layout.setSpacing(14)

        title = QtWidgets.QLabel("转换偏好")
        title.setObjectName("StatusTitle")
        layout.addWidget(title)

        caption = QtWidgets.QLabel(
            "如果生成后的 PPT 不够理想，可以先选一个优化方向，再补一句简短备注。"
            "当前版本只支持这些离线优化方向，不会联网调用 AI。"
        )
        caption.setObjectName("StatusCaption")
        caption.setWordWrap(True)
        layout.addWidget(caption)

        self.button_group = QtWidgets.QButtonGroup(self)
        option_grid = QtWidgets.QGridLayout()
        option_grid.setHorizontalSpacing(12)
        option_grid.setVerticalSpacing(12)

        for index, key in enumerate(PREFERENCE_CHOICES):
            title_text, desc = PREFERENCE_TEXT[key]
            button = QtWidgets.QRadioButton(title_text)
            button.setObjectName("PreferenceRadio")
            button.toggled.connect(self.preferencesChanged.emit)
            self.button_group.addButton(button)
            self._buttons[key] = button

            desc_label = QtWidgets.QLabel(desc)
            desc_label.setObjectName("PreferenceHint")
            desc_label.setWordWrap(True)

            wrapper = QtWidgets.QFrame()
            wrapper.setObjectName("PreferenceChoice")
            wrapper_layout = QtWidgets.QVBoxLayout(wrapper)
            wrapper_layout.setContentsMargins(16, 16, 16, 16)
            wrapper_layout.setSpacing(8)
            wrapper_layout.addWidget(button)
            wrapper_layout.addWidget(desc_label)

            option_grid.addWidget(wrapper, index // 2, index % 2)

        for column in range(2):
            option_grid.setColumnStretch(column, 1)
        layout.addLayout(option_grid)

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
            "备注只会做本地关键词映射，例如“排版、清晰、背景、速度”等词。"
        )
        self.keyword_hint.setObjectName("PreferenceHint")
        self.keyword_hint.setWordWrap(True)
        layout.addWidget(self.keyword_hint)

        self.set_preferences(TaskPreferences())

    def get_preferences(self) -> TaskPreferences:
        selected = next(
            (key for key, button in self._buttons.items() if button.isChecked()),
            PREFERENCE_LAYOUT,
        )
        return TaskPreferences(focus=selected, note=self.note_edit.toPlainText().strip()).with_mapped_tags()

    def set_preferences(self, preferences: TaskPreferences) -> None:
        preferences = TaskPreferences.from_dict(preferences.to_dict() if isinstance(preferences, TaskPreferences) else preferences)
        for key, button in self._buttons.items():
            button.setChecked(key == preferences.focus)
        self.note_edit.setPlainText(preferences.note)
