from pathlib import Path

from PyQt6 import QtCore, QtGui, QtWidgets

from services.app_models import PDF_DPI_CHOICES
from ui.icons import svg_icon


class ProgressMeter(QtWidgets.QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ProgressMeter")
        self.setFixedSize(132, 132)
        self._percent = 0

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(2)
        layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        self.percent_label = QtWidgets.QLabel("0%")
        self.percent_label.setObjectName("ProgressPercent")
        self.percent_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.percent_label)

        self.stage_label = QtWidgets.QLabel("等待任务")
        self.stage_label.setObjectName("ProgressStage")
        self.stage_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.stage_label)

    def set_status(self, percent, stage):
        self._percent = max(0, min(100, int(round(percent))))
        self.percent_label.setText(f"{self._percent}%")
        self.stage_label.setText(stage)
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)

        rect = self.rect().adjusted(14, 14, -14, -14)
        base_pen = QtGui.QPen(QtGui.QColor("#E7E9EF"), 11)
        base_pen.setCapStyle(QtCore.Qt.PenCapStyle.RoundCap)
        painter.setPen(base_pen)
        painter.drawEllipse(rect)

        progress_pen = QtGui.QPen(QtGui.QColor("#2F78FF"), 11)
        progress_pen.setCapStyle(QtCore.Qt.PenCapStyle.RoundCap)
        painter.setPen(progress_pen)
        span_angle = int(-360 * 16 * (self._percent / 100))
        painter.drawArc(rect, 90 * 16, span_angle)


class StepRow(QtWidgets.QFrame):
    def __init__(self, number, title, detail, parent=None):
        super().__init__(parent)
        self.setObjectName("ProgressStep")
        self.setMinimumHeight(72)
        layout = QtWidgets.QGridLayout(self)
        layout.setContentsMargins(0, 12, 0, 12)
        layout.setHorizontalSpacing(14)
        layout.setVerticalSpacing(4)

        self.number_label = QtWidgets.QLabel(number)
        self.number_label.setObjectName("ProgressStepNumber")
        self.number_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.number_label.setFixedWidth(46)
        layout.addWidget(self.number_label, 0, 0, 2, 1)

        self.title_label = QtWidgets.QLabel(title)
        self.title_label.setObjectName("ProgressStepTitle")
        layout.addWidget(self.title_label, 0, 1)

        self.detail_label = QtWidgets.QLabel(detail)
        self.detail_label.setObjectName("ProgressStepDetail")
        layout.addWidget(self.detail_label, 1, 1)
        self.set_state("pending")

    def set_state(self, state):
        self.setProperty("state", state)
        for widget in (self, self.number_label, self.title_label, self.detail_label):
            widget.style().unpolish(widget)
            widget.style().polish(widget)
            widget.update()


class ParameterRow(QtWidgets.QWidget):
    def __init__(self, title, parent=None):
        super().__init__(parent)
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        self.title_label = QtWidgets.QLabel(title)
        self.title_label.setObjectName("ParameterTitle")
        self.title_label.setFixedWidth(72)
        layout.addWidget(self.title_label)

        self.bar = QtWidgets.QProgressBar()
        self.bar.setObjectName("ParameterBar")
        self.bar.setRange(0, 100)
        self.bar.setTextVisible(False)
        layout.addWidget(self.bar, stretch=1)

        self.value_label = QtWidgets.QLabel("")
        self.value_label.setObjectName("ParameterValue")
        self.value_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignVCenter)
        self.value_label.setFixedWidth(74)
        layout.addWidget(self.value_label)

    def set_value(self, value, percent):
        self.value_label.setText(value)
        self.bar.setValue(max(0, min(100, int(percent))))


class SwitchControl(QtWidgets.QCheckBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(58, 32)
        self.setText("")

    def hitButton(self, pos):
        return self.rect().contains(pos)

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)

        track_rect = QtCore.QRectF(1, 1, self.width() - 2, self.height() - 2)
        track_color = QtGui.QColor("#2F78FF" if self.isChecked() else "#D8DCE6")
        if not self.isEnabled():
            track_color.setAlpha(120)
        painter.setPen(QtCore.Qt.PenStyle.NoPen)
        painter.setBrush(track_color)
        painter.drawRoundedRect(track_rect, 15, 15)

        knob_size = 24
        knob_margin = 4
        knob_x = self.width() - knob_margin - knob_size if self.isChecked() else knob_margin
        knob_rect = QtCore.QRectF(knob_x, knob_margin, knob_size, knob_size)

        shadow = QtGui.QColor(24, 27, 34, 38)
        painter.setBrush(shadow)
        painter.drawEllipse(knob_rect.translated(0, 1.4))

        painter.setBrush(QtGui.QColor("#FFFFFF"))
        painter.drawEllipse(knob_rect)


class StatusPanel(QtWidgets.QFrame):
    pickFileRequested = QtCore.pyqtSignal()
    openResultRequested = QtCore.pyqtSignal()
    openFolderRequested = QtCore.pyqtSignal()
    retryRequested = QtCore.pyqtSignal()
    scannerToggled = QtCore.pyqtSignal(bool)
    pauseRequested = QtCore.pyqtSignal()
    resumeRequested = QtCore.pyqtSignal()
    cancelRequested = QtCore.pyqtSignal()

    STAGES = (
        ("校验输入", "校验输入", "文件与参数"),
        ("提取页面", "提取页面", "PDF / 图片解析"),
        ("OCR/去字", "OCR 与净化", "文字识别、背景修复"),
        ("生成 PPTX", "生成 PPTX", "输出可编辑演示文稿"),
    )

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("StatusPanelShell")
        self.setMinimumWidth(360)
        self.current_output_path = None
        self.current_input_path = None
        self._syncing_scanner = False
        self._paused = False
        self._task_state = "idle"

        root_layout = QtWidgets.QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        scroll = QtWidgets.QScrollArea()
        scroll.setObjectName("StatusColumnScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        root_layout.addWidget(scroll)

        content = QtWidgets.QWidget()
        content_layout = QtWidgets.QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(28)
        scroll.setWidget(content)

        progress_card = QtWidgets.QFrame()
        progress_card.setObjectName("StatusPanel")
        progress_card.setMinimumHeight(1030)
        card_layout = QtWidgets.QVBoxLayout(progress_card)
        card_layout.setContentsMargins(30, 30, 30, 30)
        card_layout.setSpacing(18)
        content_layout.addWidget(progress_card)

        head_row = QtWidgets.QHBoxLayout()
        head_row.setSpacing(14)
        title = QtWidgets.QLabel("PPTX 生成进度")
        title.setObjectName("StatusTitle")
        head_row.addWidget(title)
        head_row.addStretch(1)

        pick_button = QtWidgets.QPushButton()
        pick_button.setObjectName("CircleIconButton")
        pick_button.setToolTip("选择文件")
        pick_button.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        pick_button.setFixedSize(44, 44)
        pick_button.setIcon(svg_icon("calendar", "#17191F", 20))
        pick_button.setIconSize(QtCore.QSize(20, 20))
        pick_button.clicked.connect(self.pickFileRequested.emit)
        head_row.addWidget(pick_button)
        card_layout.addLayout(head_row)

        caption = QtWidgets.QLabel("显示当前转换阶段、输出位置与结果摘要。")
        caption.setObjectName("StatusCaption")
        caption.setWordWrap(True)
        card_layout.addWidget(caption)

        self.demo_banner = QtWidgets.QLabel("演示模式已开启：可以预览界面，转换功能暂不可用。")
        self.demo_banner.setObjectName("InlineBanner")
        self.demo_banner.setWordWrap(True)
        self.demo_banner.hide()
        card_layout.addWidget(self.demo_banner)

        self.notice_banner = QtWidgets.QLabel("")
        self.notice_banner.setObjectName("MutedNotice")
        self.notice_banner.setWordWrap(True)
        self.notice_banner.hide()
        card_layout.addWidget(self.notice_banner)

        self.progress_meter = ProgressMeter()
        card_layout.addWidget(self.progress_meter, alignment=QtCore.Qt.AlignmentFlag.AlignHCenter)

        self.detail_label = QtWidgets.QLabel("选择文件后即可开始。")
        self.detail_label.setObjectName("ProgressDetail")
        self.detail_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.detail_label.setWordWrap(True)
        self.detail_label.setMinimumHeight(44)
        card_layout.addWidget(self.detail_label)

        step_list = QtWidgets.QFrame()
        step_list.setObjectName("ProgressStepList")
        step_layout = QtWidgets.QVBoxLayout(step_list)
        step_layout.setContentsMargins(0, 0, 0, 0)
        step_layout.setSpacing(0)
        self.stage_widgets = {}
        for index, (key, title_text, detail) in enumerate(self.STAGES, start=1):
            row = StepRow(f"{index:02d}", title_text, detail)
            self.stage_widgets[key] = row
            step_layout.addWidget(row)
        card_layout.addWidget(step_list)

        scanner_row = QtWidgets.QFrame()
        scanner_row.setObjectName("ToggleRow")
        scanner_layout = QtWidgets.QHBoxLayout(scanner_row)
        scanner_layout.setContentsMargins(0, 16, 0, 8)
        scanner_layout.setSpacing(18)
        scanner_text = QtWidgets.QVBoxLayout()
        scanner_text.setSpacing(4)
        scanner_title = QtWidgets.QLabel("边缘扫描裁正")
        scanner_title.setObjectName("ToggleTitle")
        scanner_text.addWidget(scanner_title)
        scanner_detail = QtWidgets.QLabel("图片任务自动弹出裁正器")
        scanner_detail.setObjectName("ToggleDetail")
        scanner_text.addWidget(scanner_detail)
        scanner_layout.addLayout(scanner_text, stretch=1)
        self.scanner_checkbox = SwitchControl()
        self.scanner_checkbox.toggled.connect(self._emit_scanner_toggled)
        scanner_layout.addWidget(self.scanner_checkbox)
        card_layout.addWidget(scanner_row)

        note_label = QtWidgets.QLabel("补充备注")
        note_label.setObjectName("MutedLabel")
        card_layout.addWidget(note_label)
        self.note_edit = QtWidgets.QPlainTextEdit()
        self.note_edit.setObjectName("TaskNoteEdit")
        self.note_edit.setPlaceholderText("例如：文字更清晰，背景残影少一些。")
        self.note_edit.setMinimumHeight(126)
        card_layout.addWidget(self.note_edit)

        self.convert_button = QtWidgets.QPushButton("开始转换")
        self.convert_button.setObjectName("PrimaryActionButton")
        self.convert_button.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self.convert_button.setIcon(svg_icon("play", "#FFFFFF", 18))
        self.convert_button.setIconSize(QtCore.QSize(18, 18))
        self.convert_button.setMinimumHeight(58)
        self.convert_button.clicked.connect(self._emit_primary_action)
        card_layout.addWidget(self.convert_button)

        self.task_controls = QtWidgets.QFrame()
        self.task_controls.setObjectName("ResultActions")
        task_control_layout = QtWidgets.QHBoxLayout(self.task_controls)
        task_control_layout.setContentsMargins(0, 0, 0, 0)
        task_control_layout.setSpacing(10)

        self.cancel_button = QtWidgets.QPushButton("取消转换")
        self.cancel_button.setObjectName("CancelActionButton")
        self.cancel_button.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self.cancel_button.setIcon(svg_icon("x", "#FFFFFF", 18))
        self.cancel_button.setIconSize(QtCore.QSize(18, 18))
        self.cancel_button.setMinimumHeight(58)
        self.cancel_button.clicked.connect(self.cancelRequested.emit)
        task_control_layout.addWidget(self.cancel_button, stretch=1)
        card_layout.addWidget(self.task_controls)

        self.result_actions = QtWidgets.QFrame()
        self.result_actions.setObjectName("ResultActions")
        action_layout = QtWidgets.QHBoxLayout(self.result_actions)
        action_layout.setContentsMargins(0, 0, 0, 0)
        action_layout.setSpacing(10)

        self.retry_button = QtWidgets.QPushButton("再次转换")
        self.retry_button.setObjectName("PrimaryActionButton")
        self.retry_button.clicked.connect(self.retryRequested.emit)
        action_layout.addWidget(self.retry_button, stretch=1)

        self.open_result_button = QtWidgets.QPushButton("打开 PPTX")
        self.open_result_button.setObjectName("ActionButton")
        self.open_result_button.clicked.connect(self.openResultRequested.emit)
        action_layout.addWidget(self.open_result_button, stretch=1)

        self.open_folder_button = QtWidgets.QPushButton("打开文件夹")
        self.open_folder_button.setObjectName("ActionButton")
        self.open_folder_button.clicked.connect(self.openFolderRequested.emit)
        action_layout.addWidget(self.open_folder_button, stretch=1)
        card_layout.addWidget(self.result_actions)

        self.summary_card = QtWidgets.QFrame()
        self.summary_card.setObjectName("SubtleCard")
        summary_layout = QtWidgets.QVBoxLayout(self.summary_card)
        summary_layout.setContentsMargins(14, 14, 14, 14)
        summary_layout.setSpacing(8)
        summary_title = QtWidgets.QLabel("结果摘要")
        summary_title.setObjectName("MutedLabel")
        summary_layout.addWidget(summary_title)
        self.summary_label = QtWidgets.QLabel("当前还没有转换结果。")
        self.summary_label.setWordWrap(True)
        self.summary_label.setObjectName("PathValue")
        summary_layout.addWidget(self.summary_label)
        card_layout.addWidget(self.summary_card)

        areas_card = QtWidgets.QFrame()
        areas_card.setObjectName("AreasCard")
        areas_layout = QtWidgets.QVBoxLayout(areas_card)
        areas_layout.setContentsMargins(24, 24, 24, 24)
        areas_layout.setSpacing(12)
        content_layout.addWidget(areas_card)

        areas_title = QtWidgets.QLabel("转换参数")
        areas_title.setObjectName("StatusTitle")
        areas_layout.addWidget(areas_title)
        areas_caption = QtWidgets.QLabel("当前任务应用的本地设置")
        areas_caption.setObjectName("StatusCaption")
        areas_layout.addWidget(areas_caption)

        self.parameter_rows = {
            "renderer": ParameterRow("Renderer"),
            "dpi": ParameterRow("PDF DPI"),
            "cleanup": ParameterRow("Cleanup"),
            "text": ParameterRow("Text"),
        }
        for row in self.parameter_rows.values():
            areas_layout.addWidget(row)

        content_layout.addStretch(1)

        self._set_result_actions_enabled(False)
        self._set_task_controls_enabled(False)
        self.retry_button.setEnabled(False)
        self.result_actions.hide()
        self.task_controls.hide()
        self.summary_card.hide()
        self._set_steps_by_index(0)
        self.progress_meter.set_status(0, "等待任务")

    def set_demo_mode(self, enabled):
        self.demo_banner.setVisible(enabled)

    def get_note(self):
        return self.note_edit.toPlainText().strip()

    def set_scanner_enabled(self, enabled):
        self._syncing_scanner = True
        try:
            self.scanner_checkbox.setChecked(bool(enabled))
        finally:
            self._syncing_scanner = False

    def set_settings(self, settings):
        renderer = getattr(settings, "preferred_renderer", "high_fidelity")
        dpi = int(getattr(settings, "pdf_quality_dpi", 200))
        cleanup = getattr(settings, "background_cleanup", "standard")
        text_mode = getattr(settings, "text_mode", "faithful")

        self.parameter_rows["renderer"].set_value("High" if renderer == "high_fidelity" else "Compat", 88 if renderer == "high_fidelity" else 56)
        try:
            dpi_index = PDF_DPI_CHOICES.index(dpi)
            dpi_meter = int(round(30 + (dpi_index / max(len(PDF_DPI_CHOICES) - 1, 1)) * 70))
        except ValueError:
            dpi_meter = 70
        self.parameter_rows["dpi"].set_value(str(dpi), dpi_meter)
        self.parameter_rows["cleanup"].set_value("Strong" if cleanup == "strong" else "Standard", 88 if cleanup == "strong" else 58)
        self.parameter_rows["text"].set_value("Clear" if text_mode == "clear" else "Faithful", 88 if text_mode == "clear" else 58)
        self.set_scanner_enabled(getattr(settings, "enable_document_scanner", False))

    def _emit_scanner_toggled(self, enabled):
        if not self._syncing_scanner:
            self.scannerToggled.emit(enabled)

    def _set_primary_button(self, text, icon_name="play", enabled=True, object_name="PrimaryActionButton"):
        self.convert_button.setStyleSheet("")
        if self.convert_button.objectName() != object_name:
            self.convert_button.setObjectName(object_name)
            self.convert_button.style().unpolish(self.convert_button)
            self.convert_button.style().polish(self.convert_button)
        self.convert_button.setText(text)
        self.convert_button.setIcon(svg_icon(icon_name, "#FFFFFF", 18))
        self.convert_button.setEnabled(enabled)
        self.convert_button.update()

    def _sync_primary_button_state(self):
        if self._task_state == "running":
            self._set_primary_button("暂停", "pause", object_name="PrimaryActionButton")
        elif self._task_state == "paused":
            self._set_primary_button("继续", "play", object_name="PausedActionButton")
        else:
            self._set_primary_button("开始转换", "play", object_name="PrimaryActionButton")

    def _emit_primary_action(self):
        if self._task_state == "idle":
            self.pickFileRequested.emit()
        elif self._task_state == "running":
            self.set_paused(True)
            self.pauseRequested.emit()
        elif self._task_state == "paused":
            self.set_paused(False)
            self.resumeRequested.emit()

    def _set_result_actions_enabled(self, enabled):
        self.open_result_button.setEnabled(enabled)
        self.open_folder_button.setEnabled(enabled)

    def _set_task_controls_enabled(self, enabled):
        self.cancel_button.setEnabled(enabled)

    def set_paused(self, paused):
        self._paused = bool(paused)
        self._task_state = "paused" if self._paused else "running"
        self._sync_primary_button_state()
        self.progress_meter.set_status(self.progress_meter._percent, "暂停中" if self._paused else "处理中")
        if self._paused:
            self.detail_label.setText("暂停请求已发送，当前页或当前阶段到达安全点后会停住。")

    def _set_notice(self, message="", notice_type="info"):
        if not message:
            self.notice_banner.hide()
            self.notice_banner.clear()
            return

        colors = {
            "info": "rgba(47, 120, 255, 0.08)",
            "warning": "rgba(255, 160, 100, 0.12)",
            "error": "rgba(255, 100, 100, 0.12)",
            "success": "rgba(77, 220, 140, 0.12)",
        }
        border = {
            "info": "rgba(47, 120, 255, 0.16)",
            "warning": "rgba(255, 160, 100, 0.30)",
            "error": "rgba(255, 100, 100, 0.30)",
            "success": "rgba(77, 220, 140, 0.30)",
        }
        self.notice_banner.setStyleSheet(
            f"background: {colors.get(notice_type, colors['info'])};"
            f"border: 1px solid {border.get(notice_type, border['info'])};"
            "border-radius: 16px; padding: 12px; color: #485160; font-weight: 800;"
        )
        self.notice_banner.setText(message)
        self.notice_banner.show()

    def _stage_index(self, stage, percent):
        aliases = {
            "校验输入": 0,
            "提取页面": 1,
            "OCR/去字": 2,
            "OCR 与净化": 2,
            "生成 PPTX": 3,
            "完成": 3,
        }
        if stage in aliases:
            return aliases[stage]
        return 3 if percent >= 78 else 2 if percent >= 42 else 1 if percent >= 18 else 0

    def _set_steps_by_index(self, active_index, done_all=False, error=False):
        for index, (key, _title, _detail) in enumerate(self.STAGES):
            row = self.stage_widgets[key]
            if error:
                row.set_state("error" if index == active_index else "pending")
            elif done_all or index < active_index:
                row.set_state("done")
            elif index == active_index:
                row.set_state("active")
            else:
                row.set_state("pending")

    def prepare_task(self, input_kind, input_path, output_path, preference_label):
        label = "PDF 转 PPTX" if input_kind == "pdf" else "图片转 PPTX"
        self.current_input_path = input_path
        self.current_output_path = output_path
        self.summary_card.show()
        self.result_actions.hide()
        self.task_controls.show()
        self._paused = False
        self._task_state = "running"
        self._sync_primary_button_state()
        self.detail_label.setText("正在检查文件与转换参数。")
        self.summary_label.setText(f"当前偏好：{preference_label}\n输出文件：{Path(output_path).name}")
        self.progress_meter.set_status(8, "校验输入")
        self._set_steps_by_index(0)
        self._set_notice()
        self.retry_button.setEnabled(False)
        self._set_result_actions_enabled(False)
        self._set_task_controls_enabled(True)

    def set_progress(self, stage, percent, detail):
        active_index = self._stage_index(stage, percent)
        display_stage = "OCR 与净化" if stage == "OCR/去字" else stage
        self.progress_meter.set_status(percent, display_stage)
        self.detail_label.setText(detail)
        self._set_steps_by_index(active_index, done_all=(stage == "完成" and percent >= 100))
        if self._task_state in {"running", "paused"}:
            self._sync_primary_button_state()

    def set_result(self, result):
        self.current_output_path = result["output_path"]
        renderer = "高保真模式" if result.get("renderer") == "node" else "兼容模式"
        self.progress_meter.set_status(100, "完成")
        self.detail_label.setText(f"已生成 {renderer} PPTX，共处理 {result['slides_processed']} 页。")
        self.summary_label.setText(
            f"输出文件：{Path(result['output_path']).name}\n当前模式：{renderer}"
        )
        self.summary_card.show()
        self._set_steps_by_index(3, done_all=True)
        if result.get("fallback_notice"):
            self._set_notice(result["fallback_notice"], "warning")
        else:
            self._set_notice("转换成功，可以直接打开结果文件或所在文件夹。", "success")
        self._task_state = "idle"
        self._sync_primary_button_state()
        self.task_controls.hide()
        self._set_task_controls_enabled(False)
        self._paused = False
        self.retry_button.setEnabled(True)
        self.result_actions.show()
        self._set_result_actions_enabled(True)

    def set_error(self, message):
        self.progress_meter.set_status(0, "转换失败")
        self.summary_card.show()
        self.detail_label.setText(message)
        self.summary_label.setText("这次转换没有成功完成。你可以调整偏好后再次转换。")
        self._set_steps_by_index(3, error=True)
        self._set_notice(message, "error")
        self._task_state = "idle"
        self._sync_primary_button_state()
        self.task_controls.hide()
        self._set_task_controls_enabled(False)
        self._paused = False
        self.retry_button.setEnabled(True)
        self.result_actions.show()
        self._set_result_actions_enabled(bool(self.current_output_path and Path(self.current_output_path).exists()))

    def show_notice(self, message):
        self.progress_meter.set_status(0, "功能提示")
        self.summary_card.show()
        self.detail_label.setText(message)
        self.summary_label.setText(message)
        self._set_notice(message, "info")
