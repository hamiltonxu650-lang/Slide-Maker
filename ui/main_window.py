from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time

from PyQt6 import QtCore, QtWidgets

from services.app_models import (
    APP_BRAND,
    OUTPUT_POLICY_ASK,
    OUTPUT_POLICY_LAST,
    OUTPUT_POLICY_SOURCE,
    PREFERENCE_CLARITY,
    PREFERENCE_CLEANUP,
    PREFERENCE_LAYOUT,
    PREFERENCE_SPEED,
    RENDERER_COMPATIBILITY,
    RENDERER_HIGH_FIDELITY,
    AppSettings,
    TaskPreferences,
    sanitize_suffix,
)
from services.platform_utils import open_path_in_shell
from services.runtime_env import describe_runtime_environment
from ui.cards import FeatureCard, PlaceholderCard
from ui.cover_config import IMAGE_HERO_IMAGE, PDF_HERO_IMAGE
from ui.preferences_panel import PREFERENCE_TEXT, PreferencePanel
from ui.settings_store import (
    app_brand,
    clear_recent_tasks,
    load_app_settings,
    load_last_preferences,
    load_recent_tasks,
    reset_app_settings,
    save_app_settings,
    save_last_preferences,
    save_recent_tasks,
)
from ui.sidebar import Sidebar
from ui.status_panel import StatusPanel
from ui.title_bar import CustomTitleBar


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class ConversionWorker(QtCore.QThread):
    progressChanged = QtCore.pyqtSignal(str, int, str)
    conversionFinished = QtCore.pyqtSignal(dict)
    conversionFailed = QtCore.pyqtSignal(str)

    def __init__(self, input_path, output_path, input_kind, settings, preferences, parent=None):
        super().__init__(parent)
        self.input_path = input_path
        self.output_path = output_path
        self.input_kind = input_kind
        self.settings = settings
        self.preferences = preferences
        self._result_payload = None
        self._error_payload = None

    def _resolve_worker_python(self):
        executable = Path(sys.executable)
        if executable.name.lower() == "pythonw.exe":
            candidate = executable.with_name("python.exe")
            if candidate.exists():
                return str(candidate)
        return str(executable)

    def _resolve_portable_worker(self):
        dist_root = Path(sys.executable).resolve().parent
        python_dir = dist_root / "portable_python"
        project_root = dist_root / "portable_app"
        site_packages = dist_root / "portable_site_packages"
        python_exe = python_dir / "python.exe"
        if python_exe.exists() and project_root.exists() and site_packages.exists():
            return {
                "python_exe": str(python_exe),
                "python_home": str(python_dir),
                "project_root": str(project_root),
                "site_packages": str(site_packages),
            }
        return None

    def _handle_protocol_line(self, line):
        handlers = {
            "GUI_PROGRESS": self._handle_progress,
            "GUI_RESULT": self._handle_result,
            "GUI_ERROR": self._handle_error,
        }
        prefix, separator, payload = line.partition("|")
        if not separator or prefix not in handlers:
            return False
        try:
            data = json.loads(payload)
        except json.JSONDecodeError:
            return False
        handlers[prefix](data)
        return True

    def _handle_progress(self, payload):
        self.progressChanged.emit(payload["stage"], int(payload["percent"]), payload["detail"])

    def _handle_result(self, payload):
        self._result_payload = payload

    def _handle_error(self, payload):
        self._error_payload = payload

    def _drain_channel_file(self, channel_path: Path, offset: int) -> int:
        if not channel_path.exists():
            return offset
        with channel_path.open("r", encoding="utf-8", errors="replace") as handle:
            handle.seek(offset)
            for raw_line in handle:
                line = raw_line.strip()
                if line:
                    self._handle_protocol_line(line)
            return handle.tell()

    def run(self):
        settings_json = json.dumps(self.settings.to_dict(), ensure_ascii=False)
        preferences_json = json.dumps(self.preferences.to_dict(), ensure_ascii=False)
        channel_path = None
        worker_cwd = str(Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else PROJECT_ROOT)
        env = os.environ.copy()
        env["PYTHONUTF8"] = "1"
        if getattr(sys, "frozen", False):
            fd, temp_path = tempfile.mkstemp(prefix="slide-maker-worker-", suffix=".jsonl")
            os.close(fd)
            channel_path = Path(temp_path)
            portable_worker = self._resolve_portable_worker()
            if portable_worker:
                project_root = Path(portable_worker["project_root"])
                command = [
                    portable_worker["python_exe"],
                    "-X",
                    "utf8",
                    str(project_root / "ui_app.py"),
                    "--worker",
                    "--input-path",
                    self.input_path,
                    "--output-path",
                    self.output_path,
                    "--input-kind",
                    self.input_kind,
                    "--settings-json",
                    settings_json,
                    "--preferences-json",
                    preferences_json,
                    "--channel-file",
                    str(channel_path),
                ]
                env["PYTHONHOME"] = portable_worker["python_home"]
                env["PYTHONPATH"] = os.pathsep.join(
                    [
                        portable_worker["project_root"],
                        portable_worker["site_packages"],
                    ]
                )
                env["PYTHONNOUSERSITE"] = "1"
                worker_cwd = portable_worker["project_root"]
            else:
                command = [
                    str(Path(sys.executable).resolve()),
                    "--worker",
                    "--input-path",
                    self.input_path,
                    "--output-path",
                    self.output_path,
                    "--input-kind",
                    self.input_kind,
                    "--settings-json",
                    settings_json,
                    "--preferences-json",
                    preferences_json,
                    "--channel-file",
                    str(channel_path),
                ]
        else:
            command = [
                self._resolve_worker_python(),
                "-X",
                "utf8",
                str(PROJECT_ROOT / "ui_app.py"),
                "--worker",
                "--input-path",
                self.input_path,
                "--output-path",
                self.output_path,
                "--input-kind",
                self.input_kind,
                "--settings-json",
                settings_json,
                "--preferences-json",
                preferences_json,
            ]
        creationflags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0

        process = subprocess.Popen(
            command,
            cwd=worker_cwd,
            stdout=None if getattr(sys, "frozen", False) else subprocess.PIPE,
            stderr=subprocess.DEVNULL if getattr(sys, "frozen", False) else subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            creationflags=creationflags,
            env=env,
        )

        if channel_path is not None:
            offset = 0
            while process.poll() is None:
                offset = self._drain_channel_file(channel_path, offset)
                time.sleep(0.1)
            offset = self._drain_channel_file(channel_path, offset)
        else:
            for raw_line in process.stdout or []:
                line = raw_line.strip()
                if not line:
                    continue
                self._handle_protocol_line(line)

        return_code = process.wait()
        if channel_path is not None:
            try:
                channel_path.unlink(missing_ok=True)
            except OSError:
                pass
        if self._result_payload is not None and return_code == 0:
            self.conversionFinished.emit(self._result_payload)
            return

        if self._error_payload is not None:
            self.conversionFailed.emit(self._error_payload.get("message", "转换失败"))
            return

        self.conversionFailed.emit(f"转换子进程退出异常，退出码 {return_code}")


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, demo_mode=False):
        super().__init__()
        self.demo_mode = demo_mode
        self.worker = None
        self.last_task = None
        self._syncing_settings = False

        self.app_settings = load_app_settings()
        self.last_preferences = load_last_preferences()
        self.recent_tasks = load_recent_tasks() if self.app_settings.remember_recent_tasks else []
        self.runtime_info = describe_runtime_environment()

        self.setWindowTitle(app_brand())
        self.setMinimumSize(1024, 720)
        self.resize(1360, 860)
        self.setWindowFlags(QtCore.Qt.WindowType.FramelessWindowHint | QtCore.Qt.WindowType.Window)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground, True)

        outer = QtWidgets.QWidget()
        outer.setObjectName("WindowRoot")
        self.outer_layout = QtWidgets.QVBoxLayout(outer)
        self.outer_layout.setContentsMargins(12, 12, 12, 12)
        self.outer_layout.setSpacing(0)

        self.surface = QtWidgets.QFrame()
        self.surface.setObjectName("AppSurface")
        surface_layout = QtWidgets.QVBoxLayout(self.surface)
        surface_layout.setContentsMargins(0, 0, 0, 0)
        surface_layout.setSpacing(0)

        self.title_bar = CustomTitleBar(self)
        surface_layout.addWidget(self.title_bar)

        body_layout = QtWidgets.QHBoxLayout()
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        self.sidebar = Sidebar()
        self.sidebar.pageSelected.connect(self._switch_page)
        body_layout.addWidget(self.sidebar)

        self.pages = QtWidgets.QStackedWidget()
        body_layout.addWidget(self.pages, stretch=1)
        surface_layout.addLayout(body_layout, stretch=1)

        grip_row = QtWidgets.QHBoxLayout()
        grip_row.setContentsMargins(0, 0, 12, 12)
        grip_row.addStretch(1)
        self.size_grip = QtWidgets.QSizeGrip(self.surface)
        self.size_grip.setStyleSheet("background: transparent;")
        grip_row.addWidget(self.size_grip, alignment=QtCore.Qt.AlignmentFlag.AlignRight)
        surface_layout.addLayout(grip_row)

        self.outer_layout.addWidget(self.surface)
        self.setCentralWidget(outer)

        self.pages.addWidget(self._build_home_page())
        self.pages.addWidget(self._build_recent_page())
        self.pages.addWidget(self._build_settings_page())
        self.pages.addWidget(self._build_about_page())

        self._apply_settings_to_controls(self.app_settings)
        self.preference_panel.set_preferences(self.last_preferences)
        self._refresh_recent_list()
        self._refresh_runtime_labels()
        self._sync_window_chrome()

        self.sidebar.select_page("home")

    def changeEvent(self, event):
        super().changeEvent(event)
        if event.type() == QtCore.QEvent.Type.WindowStateChange:
            self._sync_window_chrome()

    def showEvent(self, event):
        super().showEvent(event)
        self._sync_window_chrome()

    def _sync_window_chrome(self):
        maximized = self.isMaximized() or self.isFullScreen()
        margin = 0 if maximized else 12
        self.outer_layout.setContentsMargins(margin, margin, margin, margin)
        for widget in (self.surface, self.title_bar, self.sidebar):
            widget.setProperty("maximized", maximized)
            widget.style().unpolish(widget)
            widget.style().polish(widget)
            widget.update()
        self.title_bar.update_window_state(maximized)
        self.size_grip.setVisible(not maximized)

    def _build_home_page(self):
        page = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout(page)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        layout.addWidget(scroll, stretch=1)

        content = QtWidgets.QWidget()
        content_layout = QtWidgets.QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 6, 0)
        content_layout.setSpacing(18)
        scroll.setWidget(content)

        eyebrow = QtWidgets.QLabel("SLIDE MAKER")
        eyebrow.setObjectName("SectionEyebrow")
        content_layout.addWidget(eyebrow)

        title = QtWidgets.QLabel("各种格式转 PPTX")
        title.setObjectName("SectionTitle")
        content_layout.addWidget(title)

        caption = QtWidgets.QLabel(
            "首版启用 PDF 和图片两条真实流程，其余模块先保留产品位，方便后续继续扩展。"
        )
        caption.setObjectName("SectionCaption")
        caption.setWordWrap(True)
        content_layout.addWidget(caption)

        hero_row = QtWidgets.QHBoxLayout()
        hero_row.setSpacing(16)

        pdf_card = FeatureCard(
            "PDF 转 PPTX",
            "面向多页 PDF，自动拆页、OCR、去字，并重建可编辑幻灯片。",
            PDF_HERO_IMAGE,
            ("#8837FF", "#E23F80", "#FF6F3A"),
            "已接通",
        )
        pdf_card.clicked.connect(lambda: self.start_conversion_flow("pdf"))
        hero_row.addWidget(pdf_card, stretch=1)

        image_card = FeatureCard(
            "图片转 PPTX",
            "支持 PNG / JPG / JPEG 单图输入，适合海报、截图和设计稿首版接入。",
            IMAGE_HERO_IMAGE,
            ("#2E2A3D", "#343146", "#4D5462"),
            "已接通",
        )
        image_card.clicked.connect(lambda: self.start_conversion_flow("image"))
        hero_row.addWidget(image_card, stretch=1)
        content_layout.addLayout(hero_row)

        self.preference_panel = PreferencePanel()
        content_layout.addWidget(self.preference_panel)

        more_label = QtWidgets.QLabel("后续扩展入口")
        more_label.setStyleSheet("font-size: 20px; font-weight: 800; color: white; margin-top: 10px;")
        content_layout.addWidget(more_label)

        more_caption = QtWidgets.QLabel(
            "这些模块先保留视觉入口，点击后会提示“即将支持”，不会误触发真实转换。"
        )
        more_caption.setObjectName("SectionCaption")
        more_caption.setWordWrap(True)
        content_layout.addWidget(more_caption)

        grid = QtWidgets.QGridLayout()
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(14)

        placeholders = [
            ("Word", "计划支持 .docx 文档转 PPTX"),
            ("Excel", "计划支持表格内容重组演示文稿"),
            ("Markdown", "计划支持知识稿和笔记转 PPTX"),
            ("TXT", "计划支持纯文本大纲转幻灯片"),
            ("网页", "计划支持网页截图或 URL 页面导出"),
            ("批量导入", "计划支持文件夹与多文件队列"),
        ]
        for idx, (name, desc) in enumerate(placeholders):
            card = PlaceholderCard(name, desc)
            card.clicked.connect(self._show_coming_soon)
            grid.addWidget(card, idx // 3, idx % 3)
        for col in range(3):
            grid.setColumnStretch(col, 1)
        content_layout.addLayout(grid)
        content_layout.addStretch(1)

        self.status_panel = StatusPanel()
        self.status_panel.set_demo_mode(self.demo_mode)
        self.status_panel.openResultRequested.connect(self._open_result_file)
        self.status_panel.openFolderRequested.connect(self._open_result_folder)
        self.status_panel.retryRequested.connect(self.retry_last_task)
        layout.addWidget(self.status_panel)

        return page

    def _build_recent_page(self):
        page = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(page)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QtWidgets.QLabel("最近任务")
        title.setObjectName("SectionTitle")
        layout.addWidget(title)

        caption = QtWidgets.QLabel("这里会记录当前用户配置下的最近转换任务。")
        caption.setObjectName("SectionCaption")
        layout.addWidget(caption)

        tools_row = QtWidgets.QHBoxLayout()
        tools_row.addStretch(1)
        self.clear_recent_button = QtWidgets.QPushButton("清空记录")
        self.clear_recent_button.setObjectName("SecondaryTextButton")
        self.clear_recent_button.clicked.connect(self._clear_recent_tasks)
        tools_row.addWidget(self.clear_recent_button)
        layout.addLayout(tools_row)

        self.recent_list = QtWidgets.QListWidget()
        layout.addWidget(self.recent_list, stretch=1)
        return page

    def _build_settings_page(self):
        page = QtWidgets.QWidget()
        root_layout = QtWidgets.QVBoxLayout(page)
        root_layout.setContentsMargins(24, 24, 24, 24)
        root_layout.setSpacing(16)

        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        root_layout.addWidget(scroll)

        content = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 6, 0)
        layout.setSpacing(16)
        scroll.setWidget(content)

        title = QtWidgets.QLabel("设置")
        title.setObjectName("SectionTitle")
        layout.addWidget(title)

        caption = QtWidgets.QLabel("参考主流桌面软件的分组方式，把可真实驱动的设置集中管理。")
        caption.setObjectName("SectionCaption")
        caption.setWordWrap(True)
        layout.addWidget(caption)

        grid = QtWidgets.QGridLayout()
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(16)
        layout.addLayout(grid)

        self.general_card = self._create_setting_card("通用", "控制本地记录与恢复默认。")
        general_layout = self.general_card.layout()
        self.remember_recent_checkbox = QtWidgets.QCheckBox("记住最近任务")
        general_layout.addWidget(self.remember_recent_checkbox)
        self.restore_defaults_button = QtWidgets.QPushButton("恢复默认设置")
        self.restore_defaults_button.setObjectName("SecondaryTextButton")
        general_layout.addWidget(self.restore_defaults_button)
        grid.addWidget(self.general_card, 0, 0)

        self.output_card = self._create_setting_card("输出", "管理默认保存策略与完成后的动作。")
        output_layout = self.output_card.layout()
        self.output_policy_combo = QtWidgets.QComboBox()
        self.output_policy_combo.addItem("每次询问保存位置", OUTPUT_POLICY_ASK)
        self.output_policy_combo.addItem("默认保存到源文件同目录", OUTPUT_POLICY_SOURCE)
        self.output_policy_combo.addItem("默认保存到上次使用的目录", OUTPUT_POLICY_LAST)
        output_layout.addLayout(self._form_row("保存位置策略", self.output_policy_combo))
        self.output_suffix_edit = QtWidgets.QLineEdit()
        output_layout.addLayout(self._form_row("默认文件名后缀", self.output_suffix_edit))
        self.open_pptx_checkbox = QtWidgets.QCheckBox("完成后自动打开 PPTX")
        self.open_folder_checkbox = QtWidgets.QCheckBox("完成后自动打开文件夹")
        output_layout.addWidget(self.open_pptx_checkbox)
        output_layout.addWidget(self.open_folder_checkbox)
        grid.addWidget(self.output_card, 0, 1)

        self.conversion_card = self._create_setting_card("转换", "这些选项会进入真实转换流程。")
        conversion_layout = self.conversion_card.layout()
        self.renderer_combo = QtWidgets.QComboBox()
        self.renderer_combo.addItem("高保真优先", RENDERER_HIGH_FIDELITY)
        self.renderer_combo.addItem("兼容优先", RENDERER_COMPATIBILITY)
        conversion_layout.addLayout(self._form_row("默认渲染模式", self.renderer_combo))
        self.pdf_quality_combo = QtWidgets.QComboBox()
        for dpi in (150, 200, 300):
            self.pdf_quality_combo.addItem(f"{dpi} DPI", dpi)
        conversion_layout.addLayout(self._form_row("PDF 渲染质量", self.pdf_quality_combo))
        self.cleanup_combo = QtWidgets.QComboBox()
        self.cleanup_combo.addItem("标准", "standard")
        self.cleanup_combo.addItem("强力", "strong")
        conversion_layout.addLayout(self._form_row("背景净化强度", self.cleanup_combo))
        self.text_mode_combo = QtWidgets.QComboBox()
        self.text_mode_combo.addItem("忠实还原", "faithful")
        self.text_mode_combo.addItem("更清晰", "clear")
        conversion_layout.addLayout(self._form_row("文字模式", self.text_mode_combo))
        grid.addWidget(self.conversion_card, 1, 0)

        self.advanced_card = self._create_setting_card("高级", "查看当前运行模式、模型槽位并管理诊断信息。")
        advanced_layout = self.advanced_card.layout()
        self.diagnostics_checkbox = QtWidgets.QCheckBox("启用隐藏诊断日志")
        advanced_layout.addWidget(self.diagnostics_checkbox)
        self.runtime_mode_label = QtWidgets.QLabel("")
        self.runtime_mode_label.setObjectName("PathValue")
        self.runtime_mode_label.setWordWrap(True)
        self.runtime_mode_label.setTextInteractionFlags(QtCore.Qt.TextInteractionFlag.TextSelectableByMouse)
        advanced_layout.addLayout(self._form_row("当前运行模式", self.runtime_mode_label))
        self.runtime_dir_label = QtWidgets.QLabel("")
        self.runtime_dir_label.setObjectName("PathValue")
        self.runtime_dir_label.setWordWrap(True)
        self.runtime_dir_label.setTextInteractionFlags(QtCore.Qt.TextInteractionFlag.TextSelectableByMouse)
        advanced_layout.addLayout(self._form_row("诊断目录", self.runtime_dir_label))
        self.model_status_label = QtWidgets.QLabel("")
        self.model_status_label.setObjectName("PathValue")
        self.model_status_label.setWordWrap(True)
        self.model_status_label.setTextInteractionFlags(QtCore.Qt.TextInteractionFlag.TextSelectableByMouse)
        advanced_layout.addLayout(self._form_row("LaMa 模型状态", self.model_status_label))
        self.model_slot_label = QtWidgets.QLabel("")
        self.model_slot_label.setObjectName("PathValue")
        self.model_slot_label.setWordWrap(True)
        self.model_slot_label.setTextInteractionFlags(QtCore.Qt.TextInteractionFlag.TextSelectableByMouse)
        advanced_layout.addLayout(self._form_row("LaMa 模型槽位", self.model_slot_label))
        self.model_dir_button = QtWidgets.QPushButton("打开模型目录")
        self.model_dir_button.setObjectName("SecondaryTextButton")
        advanced_layout.addWidget(self.model_dir_button)
        self.ocr_model_status_label = QtWidgets.QLabel("")
        self.ocr_model_status_label.setObjectName("PathValue")
        self.ocr_model_status_label.setWordWrap(True)
        self.ocr_model_status_label.setTextInteractionFlags(QtCore.Qt.TextInteractionFlag.TextSelectableByMouse)
        advanced_layout.addLayout(self._form_row("OCR 模型状态", self.ocr_model_status_label))
        self.ocr_model_slot_label = QtWidgets.QLabel("")
        self.ocr_model_slot_label.setObjectName("PathValue")
        self.ocr_model_slot_label.setWordWrap(True)
        self.ocr_model_slot_label.setTextInteractionFlags(QtCore.Qt.TextInteractionFlag.TextSelectableByMouse)
        advanced_layout.addLayout(self._form_row("OCR 模型槽位", self.ocr_model_slot_label))
        self.ocr_model_dir_button = QtWidgets.QPushButton("打开 OCR 模型目录")
        self.ocr_model_dir_button.setObjectName("SecondaryTextButton")
        advanced_layout.addWidget(self.ocr_model_dir_button)
        self.diagnostic_dir_button = QtWidgets.QPushButton("打开诊断目录")
        self.diagnostic_dir_button.setObjectName("SecondaryTextButton")
        advanced_layout.addWidget(self.diagnostic_dir_button)
        grid.addWidget(self.advanced_card, 1, 1)

        for column in range(2):
            grid.setColumnStretch(column, 1)

        self._connect_settings_signals()
        return page

    def _build_about_page(self):
        page = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(page)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        card = QtWidgets.QFrame()
        card.setObjectName("InfoPageCard")
        card_layout = QtWidgets.QVBoxLayout(card)
        card_layout.setContentsMargins(22, 22, 22, 22)
        card_layout.setSpacing(12)

        title = QtWidgets.QLabel("关于")
        title.setObjectName("SectionTitle")
        card_layout.addWidget(title)

        texts = [
            f"{APP_BRAND} 是围绕现有 OCR、去字与 PPTX 生成引擎搭建的离线桌面版。",
            "演示模式命令：python ui_app.py --demo",
            "真实模式命令：python ui_app.py",
            "推荐样例：test\\Quiz 1.pdf 与 test\\未命名的设计.png",
        ]
        for text in texts:
            label = QtWidgets.QLabel(text)
            label.setWordWrap(True)
            label.setObjectName("SectionCaption")
            card_layout.addWidget(label)

        layout.addWidget(card)
        layout.addStretch(1)
        return page

    def _create_setting_card(self, title, caption):
        card = QtWidgets.QFrame()
        card.setObjectName("SettingCard")
        layout = QtWidgets.QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title_label = QtWidgets.QLabel(title)
        title_label.setObjectName("SettingTitle")
        layout.addWidget(title_label)

        caption_label = QtWidgets.QLabel(caption)
        caption_label.setObjectName("SettingCaption")
        caption_label.setWordWrap(True)
        layout.addWidget(caption_label)
        return card

    def _form_row(self, label_text, widget):
        row = QtWidgets.QVBoxLayout()
        row.setSpacing(6)
        label = QtWidgets.QLabel(label_text)
        label.setObjectName("MutedLabel")
        row.addWidget(label)
        row.addWidget(widget)
        return row

    def _connect_settings_signals(self):
        controls = [
            self.remember_recent_checkbox,
            self.output_policy_combo,
            self.output_suffix_edit,
            self.open_pptx_checkbox,
            self.open_folder_checkbox,
            self.renderer_combo,
            self.pdf_quality_combo,
            self.cleanup_combo,
            self.text_mode_combo,
            self.diagnostics_checkbox,
        ]
        for widget in controls:
            if isinstance(widget, QtWidgets.QComboBox):
                widget.currentIndexChanged.connect(self._store_settings_from_controls)
            elif isinstance(widget, QtWidgets.QLineEdit):
                widget.editingFinished.connect(self._store_settings_from_controls)
            else:
                widget.toggled.connect(self._store_settings_from_controls)

        self.restore_defaults_button.clicked.connect(self._restore_defaults)
        self.model_dir_button.clicked.connect(self._open_model_dir)
        self.ocr_model_dir_button.clicked.connect(self._open_ocr_model_dir)
        self.diagnostic_dir_button.clicked.connect(self._open_diagnostic_dir)

    def _apply_settings_to_controls(self, settings: AppSettings):
        self._syncing_settings = True
        try:
            self.remember_recent_checkbox.setChecked(settings.remember_recent_tasks)
            self.output_policy_combo.setCurrentIndex(
                max(0, self.output_policy_combo.findData(settings.output_location_policy))
            )
            self.output_suffix_edit.setText(settings.output_suffix)
            self.open_pptx_checkbox.setChecked(settings.open_pptx_after_conversion)
            self.open_folder_checkbox.setChecked(settings.open_folder_after_conversion)
            self.renderer_combo.setCurrentIndex(max(0, self.renderer_combo.findData(settings.preferred_renderer)))
            self.pdf_quality_combo.setCurrentIndex(max(0, self.pdf_quality_combo.findData(settings.pdf_quality_dpi)))
            self.cleanup_combo.setCurrentIndex(max(0, self.cleanup_combo.findData(settings.background_cleanup)))
            self.text_mode_combo.setCurrentIndex(max(0, self.text_mode_combo.findData(settings.text_mode)))
            self.diagnostics_checkbox.setChecked(settings.diagnostic_logs)
        finally:
            self._syncing_settings = False

    def _collect_settings_from_controls(self) -> AppSettings:
        return AppSettings(
            remember_recent_tasks=self.remember_recent_checkbox.isChecked(),
            output_location_policy=self.output_policy_combo.currentData(),
            last_output_dir=self.app_settings.last_output_dir,
            output_suffix=sanitize_suffix(self.output_suffix_edit.text()),
            open_pptx_after_conversion=self.open_pptx_checkbox.isChecked(),
            open_folder_after_conversion=self.open_folder_checkbox.isChecked(),
            preferred_renderer=self.renderer_combo.currentData(),
            pdf_quality_dpi=int(self.pdf_quality_combo.currentData()),
            background_cleanup=self.cleanup_combo.currentData(),
            text_mode=self.text_mode_combo.currentData(),
            diagnostic_logs=self.diagnostics_checkbox.isChecked(),
        )

    def _store_settings_from_controls(self):
        if self._syncing_settings:
            return
        self.app_settings = self._collect_settings_from_controls()
        save_app_settings(self.app_settings)
        self.output_suffix_edit.setText(self.app_settings.output_suffix)
        if not self.app_settings.remember_recent_tasks:
            self.recent_tasks = []
            clear_recent_tasks()
            self._refresh_recent_list()
        self._refresh_runtime_labels()

    def _restore_defaults(self):
        self.app_settings = reset_app_settings()
        self._apply_settings_to_controls(self.app_settings)
        if not self.app_settings.remember_recent_tasks:
            self.recent_tasks = []
            clear_recent_tasks()
        self._refresh_recent_list()
        self._refresh_runtime_labels()

    def _refresh_runtime_labels(self):
        self.runtime_info = describe_runtime_environment()
        if self.runtime_info["high_fidelity_available"]:
            runtime_text = "高保真运行时可用"
        else:
            runtime_text = "仅兼容模式"
        log_dir = self.runtime_info["log_dir"]
        self.runtime_mode_label.setText(runtime_text)
        self.runtime_dir_label.setText(log_dir)
        self.model_status_label.setText(self.runtime_info["lama_model_message"])
        self.model_slot_label.setText(self.runtime_info["lama_model_slot"])
        self.ocr_model_status_label.setText(self.runtime_info["ocr_model_message"])
        self.ocr_model_slot_label.setText(self.runtime_info["ocr_model_slot_dir"])

    def _refresh_recent_list(self):
        self.recent_list.clear()
        if not self.recent_tasks:
            self.recent_list.addItem("还没有任务记录。完成一次转换后会出现在这里。")
        else:
            self.recent_list.addItems(self.recent_tasks[:20])
        self.clear_recent_button.setEnabled(bool(self.recent_tasks))

    def _clear_recent_tasks(self):
        self.recent_tasks = []
        clear_recent_tasks()
        self._refresh_recent_list()

    def _preference_label(self, preferences: TaskPreferences) -> str:
        return PREFERENCE_TEXT.get(preferences.focus, PREFERENCE_TEXT[PREFERENCE_LAYOUT])[0]

    def _switch_page(self, key):
        mapping = {"home": 0, "recent": 1, "settings": 2, "about": 3}
        page_key = key if key in mapping else "home"
        self.pages.setCurrentIndex(mapping[page_key])

    def _show_coming_soon(self, title):
        self.status_panel.show_notice(f"{title} 模块即将支持，当前版本不会触发真实转换。")
        self.sidebar.select_page("home")

    def _build_file_filter(self, input_kind):
        return "PDF 文件 (*.pdf)" if input_kind == "pdf" else "图片文件 (*.png *.jpg *.jpeg)"

    def _build_default_output_name(self, input_path: str) -> str:
        suffix = sanitize_suffix(self.app_settings.output_suffix)
        return f"{Path(input_path).stem}{suffix}.pptx"

    def _make_unique_output_path(self, candidate: Path) -> Path:
        if not candidate.exists():
            return candidate
        stem = candidate.stem
        suffix = candidate.suffix
        for index in range(2, 100):
            sibling = candidate.with_name(f"{stem}_{index}{suffix}")
            if not sibling.exists():
                return sibling
        return candidate.with_name(f"{stem}_{QtCore.QDateTime.currentDateTime().toString('yyyyMMddHHmmss')}{suffix}")

    def _choose_output_path(self, input_path: str) -> str | None:
        input_file = Path(input_path)
        output_name = self._build_default_output_name(input_path)
        policy = self.app_settings.output_location_policy

        if policy == OUTPUT_POLICY_SOURCE:
            target_dir = input_file.parent
            output_path = self._make_unique_output_path(target_dir / output_name)
        elif policy == OUTPUT_POLICY_LAST and self.app_settings.last_output_dir:
            target_dir = Path(self.app_settings.last_output_dir)
            if not target_dir.exists():
                target_dir = input_file.parent
            output_path = self._make_unique_output_path(target_dir / output_name)
        else:
            start_dir = Path(self.app_settings.last_output_dir) if self.app_settings.last_output_dir else input_file.parent
            default_output = str(start_dir / output_name)
            output_path, _ = QtWidgets.QFileDialog.getSaveFileName(
                self,
                "选择输出 PPTX",
                default_output,
                "PowerPoint 演示文稿 (*.pptx)",
            )
            if not output_path:
                return None
            if not output_path.lower().endswith(".pptx"):
                output_path += ".pptx"
            target_dir = Path(output_path).parent
            self.app_settings.last_output_dir = str(target_dir)
            save_app_settings(self.app_settings)
            return output_path

        self.app_settings.last_output_dir = str(output_path.parent)
        save_app_settings(self.app_settings)
        return str(output_path)

    def start_conversion_flow(self, input_kind):
        if self.worker and self.worker.isRunning():
            self.status_panel.show_notice("当前已有任务在执行，请等待完成后再发起新任务。")
            return

        if self.demo_mode:
            label = "PDF 转 PPTX" if input_kind == "pdf" else "图片转 PPTX"
            self.status_panel.show_notice(f"{label} 入口在演示模式下只展示界面，不执行真实转换。")
            return

        input_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "选择输入文件",
            str(PROJECT_ROOT / "test"),
            self._build_file_filter(input_kind),
        )
        if not input_path:
            return

        output_path = self._choose_output_path(input_path)
        if not output_path:
            return

        preferences = self.preference_panel.get_preferences()
        self._launch_worker(input_path, output_path, input_kind, preferences)

    def _launch_worker(self, input_path, output_path, input_kind, preferences: TaskPreferences):
        self.last_task = {
            "input_path": input_path,
            "output_path": output_path,
            "input_kind": input_kind,
            "preferences": preferences.to_dict(),
        }
        self.last_preferences = preferences
        save_last_preferences(preferences)

        self.sidebar.select_page("home")
        self.status_panel.prepare_task(
            input_kind,
            input_path,
            output_path,
            self._preference_label(preferences),
        )

        self.worker = ConversionWorker(input_path, output_path, input_kind, self.app_settings, preferences, self)
        self.worker.progressChanged.connect(self.status_panel.set_progress)
        self.worker.conversionFinished.connect(self._handle_success)
        self.worker.conversionFailed.connect(self._handle_failure)
        self.worker.finished.connect(self._cleanup_worker)
        self.worker.start()

    def retry_last_task(self):
        if not self.last_task:
            self.status_panel.show_notice("还没有可重试的任务。")
            return
        if self.worker and self.worker.isRunning():
            return
        preferences = TaskPreferences.from_dict(self.last_task.get("preferences"))
        self.preference_panel.set_preferences(preferences)
        self._launch_worker(
            self.last_task["input_path"],
            self.last_task["output_path"],
            self.last_task["input_kind"],
            preferences,
        )

    def _record_recent_task(self, message: str):
        if not self.app_settings.remember_recent_tasks:
            return
        self.recent_tasks.insert(0, message)
        self.recent_tasks = self.recent_tasks[:20]
        save_recent_tasks(self.recent_tasks)
        self._refresh_recent_list()

    def _handle_success(self, result):
        self.status_panel.set_result(result)
        mode_text = "高保真完成" if result.get("renderer") == "node" else "兼容完成"
        record = f"{mode_text} | {Path(result['input_path']).name} -> {Path(result['output_path']).name}"
        self._record_recent_task(record)
        self._refresh_runtime_labels()

        if self.app_settings.open_pptx_after_conversion:
            self._open_result_file()
        if self.app_settings.open_folder_after_conversion:
            self._open_result_folder()

    def _handle_failure(self, message):
        self.status_panel.set_error(message)
        failed_output = Path(self.last_task["output_path"]).name if self.last_task else "未知输出"
        self._record_recent_task(f"失败 | {failed_output} | {message}")

    def _cleanup_worker(self):
        self.worker = None

    def _open_result_file(self):
        path = self.status_panel.current_output_path
        if path and Path(path).exists():
            if not open_path_in_shell(path):
                self.status_panel.show_notice("无法打开结果文件，请手动到输出目录查看。")
        else:
            self.status_panel.show_notice("结果文件还不存在，先完成一次转换。")

    def _open_result_folder(self):
        path = self.status_panel.current_output_path
        if path and Path(path).exists():
            if not open_path_in_shell(Path(path).parent):
                self.status_panel.show_notice("无法打开输出文件夹，请手动到输出目录查看。")
        else:
            self.status_panel.show_notice("结果文件夹还不可用，先完成一次转换。")

    def _open_diagnostic_dir(self):
        log_dir = Path(self.runtime_info["log_dir"])
        log_dir.mkdir(parents=True, exist_ok=True)
        if not open_path_in_shell(log_dir):
            self.status_panel.show_notice("无法打开诊断目录，请手动到日志目录查看。")

    def _open_model_dir(self):
        model_dir = Path(self.runtime_info["lama_model_slot"]).parent
        model_dir.mkdir(parents=True, exist_ok=True)
        if not open_path_in_shell(model_dir):
            self.status_panel.show_notice("无法打开模型目录，请手动到模型槽位目录查看。")

    def _open_ocr_model_dir(self):
        model_dir = Path(self.runtime_info["ocr_model_slot_dir"])
        model_dir.mkdir(parents=True, exist_ok=True)
        if not open_path_in_shell(model_dir):
            self.status_panel.show_notice("无法打开 OCR 模型目录，请手动到 OCR 模型槽位目录查看。")
