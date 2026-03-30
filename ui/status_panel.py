from pathlib import Path

from PyQt6 import QtCore, QtGui, QtWidgets


class PathField(QtWidgets.QLineEdit):
    def __init__(self, text="", parent=None):
        super().__init__(parent)
        self.setObjectName("PathField")
        self.setReadOnly(True)
        self.setMinimumHeight(38)
        self.setCursorPosition(0)
        self.set_path_text(text)

    def set_path_text(self, text):
        value = str(text or "")
        self.setText(value)
        self.setToolTip(value)
        self.setCursorPosition(0)


class StageIndicator(QtWidgets.QFrame):
    def __init__(self, title, parent=None):
        super().__init__(parent)
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        self.dot = QtWidgets.QLabel()
        self.dot.setFixedSize(12, 12)
        layout.addWidget(self.dot, alignment=QtCore.Qt.AlignmentFlag.AlignTop)

        text_layout = QtWidgets.QVBoxLayout()
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(2)

        self.title_label = QtWidgets.QLabel(title)
        self.title_label.setObjectName("StageTitle")
        text_layout.addWidget(self.title_label)

        self.detail_label = QtWidgets.QLabel("等待中")
        self.detail_label.setObjectName("StageDetail")
        text_layout.addWidget(self.detail_label)
        layout.addLayout(text_layout, stretch=1)
        self.set_state("pending", "等待中")

    def set_state(self, state, detail=None):
        palette = {
            "pending": ("#3A354F", "#8F88AA", "#6A637F"),
            "active": ("#FF8A4C", "#FFFFFF", "#E6C8A7"),
            "done": ("#4DDC8C", "#F4F0FF", "#AEE7C5"),
            "error": ("#FF6464", "#FFFFFF", "#FFC4C4"),
        }
        dot, title, detail_color = palette.get(state, palette["pending"])
        self.dot.setStyleSheet(f"background: {dot}; border-radius: 6px;")
        self.title_label.setStyleSheet(f"font-weight: 700; color: {title};")
        self.detail_label.setStyleSheet(f"font-size: 12px; color: {detail_color};")
        if detail:
            self.detail_label.setText(detail)


class StatusPanel(QtWidgets.QFrame):
    openResultRequested = QtCore.pyqtSignal()
    openFolderRequested = QtCore.pyqtSignal()
    retryRequested = QtCore.pyqtSignal()

    STAGES = ["校验输入", "提取页面", "OCR/去字", "生成 PPTX", "完成"]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("StatusPanel")
        self.setMinimumWidth(360)
        self.current_output_path = None
        self.current_input_path = None

        root_layout = QtWidgets.QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        root_layout.addWidget(scroll)

        content = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(content)
        layout.setContentsMargins(22, 22, 22, 22)
        layout.setSpacing(16)
        scroll.setWidget(content)

        title = QtWidgets.QLabel("任务状态")
        title.setObjectName("StatusTitle")
        layout.addWidget(title)

        caption = QtWidgets.QLabel("实时显示当前转换阶段、输出位置与结果摘要。")
        caption.setObjectName("StatusCaption")
        caption.setWordWrap(True)
        layout.addWidget(caption)

        self.demo_banner = QtWidgets.QLabel("演示模式已开启：可以预览界面，但不会执行真实转换。")
        self.demo_banner.setObjectName("InlineBanner")
        self.demo_banner.setWordWrap(True)
        self.demo_banner.hide()
        layout.addWidget(self.demo_banner)

        self.notice_banner = QtWidgets.QLabel("")
        self.notice_banner.setObjectName("MutedNotice")
        self.notice_banner.setWordWrap(True)
        self.notice_banner.hide()
        layout.addWidget(self.notice_banner)

        self.state_label = QtWidgets.QLabel("空闲中")
        self.state_label.setStyleSheet("font-size: 16px; font-weight: 800; color: #FFFFFF;")
        layout.addWidget(self.state_label)

        self.detail_label = QtWidgets.QLabel("选择左侧入口开始转换。")
        self.detail_label.setWordWrap(True)
        self.detail_label.setObjectName("StatusCaption")
        layout.addWidget(self.detail_label)

        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        self.stage_widgets = {}
        for stage in self.STAGES:
            widget = StageIndicator(stage)
            self.stage_widgets[stage] = widget
            layout.addWidget(widget)

        path_group = QtWidgets.QFrame()
        path_group.setObjectName("SubtleCard")
        path_layout = QtWidgets.QVBoxLayout(path_group)
        path_layout.setContentsMargins(16, 16, 16, 16)
        path_layout.setSpacing(10)

        in_label = QtWidgets.QLabel("输入文件")
        in_label.setObjectName("MutedLabel")
        path_layout.addWidget(in_label)

        self.input_path_label = PathField("尚未选择")
        path_layout.addWidget(self.input_path_label)

        out_label = QtWidgets.QLabel("输出文件")
        out_label.setObjectName("MutedLabel")
        path_layout.addWidget(out_label)

        self.output_path_label = PathField("尚未选择")
        path_layout.addWidget(self.output_path_label)
        layout.addWidget(path_group)

        self.summary_card = QtWidgets.QFrame()
        self.summary_card.setObjectName("SubtleCard")
        summary_layout = QtWidgets.QVBoxLayout(self.summary_card)
        summary_layout.setContentsMargins(16, 16, 16, 16)
        summary_layout.setSpacing(8)

        summary_title = QtWidgets.QLabel("结果摘要")
        summary_title.setObjectName("MutedLabel")
        summary_layout.addWidget(summary_title)

        self.summary_label = QtWidgets.QLabel("当前还没有转换结果。")
        self.summary_label.setWordWrap(True)
        self.summary_label.setObjectName("PathValue")
        summary_layout.addWidget(self.summary_label)
        layout.addWidget(self.summary_card)

        button_row = QtWidgets.QHBoxLayout()
        button_row.setSpacing(10)

        self.retry_button = QtWidgets.QPushButton("再次转换")
        self.retry_button.setObjectName("PrimaryActionButton")
        self.retry_button.clicked.connect(self.retryRequested.emit)
        button_row.addWidget(self.retry_button, stretch=1)

        self.open_result_button = QtWidgets.QPushButton("打开 PPTX")
        self.open_result_button.setObjectName("ActionButton")
        self.open_result_button.clicked.connect(self.openResultRequested.emit)
        button_row.addWidget(self.open_result_button, stretch=1)

        self.open_folder_button = QtWidgets.QPushButton("打开文件夹")
        self.open_folder_button.setObjectName("ActionButton")
        self.open_folder_button.clicked.connect(self.openFolderRequested.emit)
        button_row.addWidget(self.open_folder_button, stretch=1)
        layout.addLayout(button_row)
        layout.addStretch(1)

        self._set_result_actions_enabled(False)
        self.retry_button.setEnabled(False)

    def set_demo_mode(self, enabled):
        self.demo_banner.setVisible(enabled)

    def _set_result_actions_enabled(self, enabled):
        self.open_result_button.setEnabled(enabled)
        self.open_folder_button.setEnabled(enabled)

    def _set_notice(self, message="", notice_type="info"):
        if not message:
            self.notice_banner.hide()
            self.notice_banner.clear()
            return

        colors = {
            "info": "rgba(255, 176, 109, 0.10)",
            "warning": "rgba(255, 160, 100, 0.12)",
            "error": "rgba(255, 100, 100, 0.12)",
            "success": "rgba(77, 220, 140, 0.12)",
        }
        border = {
            "info": "rgba(255, 176, 109, 0.28)",
            "warning": "rgba(255, 160, 100, 0.30)",
            "error": "rgba(255, 100, 100, 0.30)",
            "success": "rgba(77, 220, 140, 0.30)",
        }
        self.notice_banner.setStyleSheet(
            f"background: {colors.get(notice_type, colors['info'])};"
            f"border: 1px solid {border.get(notice_type, border['info'])};"
            "border-radius: 14px; padding: 12px; color: #F3E7D9; font-weight: 700;"
        )
        self.notice_banner.setText(message)
        self.notice_banner.show()

    def prepare_task(self, input_kind, input_path, output_path, preference_label):
        label = "PDF 转 PPTX" if input_kind == "pdf" else "图片转 PPTX"
        self.current_input_path = input_path
        self.current_output_path = output_path
        self.state_label.setText(f"{label} 执行中")
        self.detail_label.setText("任务已启动，正在准备底层转换流程。")
        self.summary_label.setText(f"当前偏好：{preference_label}")
        self.progress_bar.setValue(0)
        self.input_path_label.set_path_text(input_path)
        self.output_path_label.set_path_text(output_path)
        self._set_notice()
        for stage in self.STAGES:
            self.stage_widgets[stage].set_state("pending", "等待中")
        self.retry_button.setEnabled(False)
        self._set_result_actions_enabled(False)

    def set_progress(self, stage, percent, detail):
        self.progress_bar.setValue(percent)
        self.detail_label.setText(detail)
        reached_current = False
        for stage_name in self.STAGES:
            widget = self.stage_widgets[stage_name]
            if stage_name == stage:
                widget.set_state("active", detail)
                reached_current = True
                continue
            if not reached_current:
                widget.set_state("done", "已完成")
            else:
                widget.set_state("pending", "等待中")
        self.state_label.setText("转换完成" if stage == "完成" and percent >= 100 else f"{stage} · {percent}%")

    def set_result(self, result):
        self.current_output_path = result["output_path"]
        renderer = "高保真模式" if result.get("renderer") == "node" else "兼容模式"
        self.state_label.setText("转换完成")
        self.detail_label.setText(f"已生成 {renderer} PPTX，共处理 {result['slides_processed']} 页。")
        self.summary_label.setText(
            f"输出文件：{Path(result['output_path']).name}\n当前模式：{renderer}"
        )
        self.progress_bar.setValue(100)
        for stage_name, widget in self.stage_widgets.items():
            widget.set_state("done", "已完成" if stage_name != "完成" else "可以打开结果文件")
        if result.get("fallback_notice"):
            self._set_notice(result["fallback_notice"], "warning")
        else:
            self._set_notice("转换成功，可以直接打开结果文件或所在文件夹。", "success")
        self.retry_button.setEnabled(True)
        self._set_result_actions_enabled(True)

    def set_error(self, message):
        self.state_label.setText("转换失败")
        self.detail_label.setText(message)
        self.summary_label.setText("这次转换没有成功完成。你可以调整偏好后再次转换。")
        for stage in self.STAGES:
            self.stage_widgets[stage].set_state("error" if stage == "完成" else "pending", message if stage == "完成" else "等待中")
        self._set_notice(message, "error")
        self.retry_button.setEnabled(True)
        self._set_result_actions_enabled(bool(self.current_output_path and Path(self.current_output_path).exists()))

    def show_notice(self, message):
        self.state_label.setText("功能提示")
        self.detail_label.setText(message)
        self.summary_label.setText(message)
        self._set_notice(message, "info")
