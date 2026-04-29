from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time

from PyQt6 import QtCore, QtGui, QtWidgets

from services.app_models import (
    APP_BRAND,
    OUTPUT_POLICY_ASK,
    OUTPUT_POLICY_LAST,
    OUTPUT_POLICY_SOURCE,
    PDF_DPI_CHOICES,
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
from ui.icons import sharp_pixmap, svg_icon, svg_pixmap
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
GITHUB_PROJECT_URL = "https://github.com/hamiltonxu650-lang/Slide-Maker"
COMMON_IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg"}
MAC_ONLY_IMAGE_SUFFIXES = {".heic", ".heif"}


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
        self._use_native_macos_chrome = sys.platform == "darwin"

        self.app_settings = load_app_settings()
        self.last_preferences = load_last_preferences()
        self.recent_tasks = load_recent_tasks() if self.app_settings.remember_recent_tasks else []
        self.runtime_info = describe_runtime_environment()

        self.setWindowTitle(app_brand())
        self.setMinimumSize(1024, 720)
        self.resize(1360, 860)
        if self._use_native_macos_chrome:
            self.setWindowFlags(
                QtCore.Qt.WindowType.Window
                | QtCore.Qt.WindowType.WindowMinimizeButtonHint
                | QtCore.Qt.WindowType.WindowMaximizeButtonHint
                | QtCore.Qt.WindowType.WindowCloseButtonHint
            )
            self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground, False)
        else:
            self.setWindowFlags(QtCore.Qt.WindowType.FramelessWindowHint | QtCore.Qt.WindowType.Window)
            self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground, True)

        outer = QtWidgets.QWidget()
        outer.setObjectName("WindowRoot")
        self.outer_layout = QtWidgets.QVBoxLayout(outer)
        initial_margin = 0 if self._use_native_macos_chrome else 12
        self.outer_layout.setContentsMargins(initial_margin, initial_margin, initial_margin, initial_margin)
        self.outer_layout.setSpacing(0)

        self.surface = QtWidgets.QFrame()
        self.surface.setObjectName("AppSurface")
        self.surface.setProperty("nativeMacChrome", self._use_native_macos_chrome)
        surface_layout = QtWidgets.QVBoxLayout(self.surface)
        surface_layout.setContentsMargins(0, 0, 0, 0)
        surface_layout.setSpacing(0)

        self.title_bar = None
        if not self._use_native_macos_chrome:
            self.title_bar = CustomTitleBar(self)
            surface_layout.addWidget(self.title_bar)

        body_layout = QtWidgets.QHBoxLayout()
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        self.sidebar = Sidebar()
        self.sidebar.setProperty("nativeMacChrome", self._use_native_macos_chrome)
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

        # Build native macOS global menu bar (must be after pages are built)
        if sys.platform == "darwin":
            self._build_mac_menu_bar()

        self.sidebar.select_page("home")

    # ------------------------------------------------------------------
    # macOS native global menu bar
    # ------------------------------------------------------------------
    def _build_mac_menu_bar(self):
        """Create a real, functional macOS global menu bar."""
        from PyQt6 import QtGui

        menu_bar = self.menuBar()
        menu_bar.setNativeMenuBar(True)

        # ── App menu (Slide Maker) ──
        # On macOS, the app menu is auto-created from QApplication name.
        # We add items that macOS expects to find in the app menu.

        # ── File ──
        file_menu = menu_bar.addMenu("文件")

        open_pdf_action = QtGui.QAction("转换 PDF…", self)
        open_pdf_action.setShortcut(QtGui.QKeySequence("Ctrl+O"))
        open_pdf_action.triggered.connect(lambda: self.start_conversion_flow("pdf"))
        file_menu.addAction(open_pdf_action)

        open_image_action = QtGui.QAction("转换图片…", self)
        open_image_action.setShortcut(QtGui.QKeySequence("Shift+Ctrl+O"))
        open_image_action.triggered.connect(lambda: self.start_conversion_flow("image"))
        file_menu.addAction(open_image_action)

        file_menu.addSeparator()

        open_result_action = QtGui.QAction("打开结果文件", self)
        open_result_action.triggered.connect(self._open_result_file)
        file_menu.addAction(open_result_action)

        open_folder_action = QtGui.QAction("打开结果文件夹", self)
        open_folder_action.triggered.connect(self._open_result_folder)
        file_menu.addAction(open_folder_action)

        file_menu.addSeparator()

        close_action = QtGui.QAction("关闭窗口", self)
        close_action.setShortcut(QtGui.QKeySequence("Ctrl+W"))
        close_action.triggered.connect(self.close)
        file_menu.addAction(close_action)

        # ── Edit ──
        edit_menu = menu_bar.addMenu("编辑")

        undo_action = QtGui.QAction("撤销", self)
        undo_action.setShortcut(QtGui.QKeySequence.StandardKey.Undo)
        edit_menu.addAction(undo_action)

        redo_action = QtGui.QAction("重做", self)
        redo_action.setShortcut(QtGui.QKeySequence.StandardKey.Redo)
        edit_menu.addAction(redo_action)

        edit_menu.addSeparator()

        cut_action = QtGui.QAction("剪切", self)
        cut_action.setShortcut(QtGui.QKeySequence.StandardKey.Cut)
        edit_menu.addAction(cut_action)

        copy_action = QtGui.QAction("拷贝", self)
        copy_action.setShortcut(QtGui.QKeySequence.StandardKey.Copy)
        edit_menu.addAction(copy_action)

        paste_action = QtGui.QAction("粘贴", self)
        paste_action.setShortcut(QtGui.QKeySequence.StandardKey.Paste)
        edit_menu.addAction(paste_action)

        select_all_action = QtGui.QAction("全选", self)
        select_all_action.setShortcut(QtGui.QKeySequence.StandardKey.SelectAll)
        edit_menu.addAction(select_all_action)

        # Wire Edit actions to the currently focused widget
        for action, slot_name in [
            (undo_action, "undo"), (redo_action, "redo"),
            (cut_action, "cut"), (copy_action, "copy"),
            (paste_action, "paste"), (select_all_action, "selectAll"),
        ]:
            action.triggered.connect(self._make_focus_slot(slot_name))

        # ── View ──
        view_menu = menu_bar.addMenu("显示")

        home_action = QtGui.QAction("首页", self)
        home_action.setShortcut(QtGui.QKeySequence("Ctrl+1"))
        home_action.triggered.connect(lambda: self._menu_switch_page("home"))
        view_menu.addAction(home_action)

        recent_action = QtGui.QAction("最近任务", self)
        recent_action.setShortcut(QtGui.QKeySequence("Ctrl+2"))
        recent_action.triggered.connect(lambda: self._menu_switch_page("recent"))
        view_menu.addAction(recent_action)

        settings_action = QtGui.QAction("设置", self)
        settings_action.setShortcut(QtGui.QKeySequence("Ctrl+,"))
        settings_action.setMenuRole(QtGui.QAction.MenuRole.PreferencesRole)
        settings_action.triggered.connect(lambda: self._menu_switch_page("settings"))
        view_menu.addAction(settings_action)

        about_action = QtGui.QAction(f"关于 {APP_BRAND}", self)
        about_action.setMenuRole(QtGui.QAction.MenuRole.AboutRole)
        about_action.triggered.connect(lambda: self._menu_switch_page("about"))
        view_menu.addAction(about_action)

        view_menu.addSeparator()

        fullscreen_action = QtGui.QAction("进入/退出全屏", self)
        fullscreen_action.setShortcut(QtGui.QKeySequence("Meta+Ctrl+F"))
        fullscreen_action.triggered.connect(self._menu_toggle_fullscreen)
        view_menu.addAction(fullscreen_action)

        # ── Window ──
        window_menu = menu_bar.addMenu("窗口")

        minimize_action = QtGui.QAction("最小化", self)
        minimize_action.setShortcut(QtGui.QKeySequence("Ctrl+M"))
        minimize_action.triggered.connect(self.showMinimized)
        window_menu.addAction(minimize_action)

        zoom_action = QtGui.QAction("缩放", self)
        zoom_action.triggered.connect(self._menu_toggle_fullscreen)
        window_menu.addAction(zoom_action)

        # ── Help ──
        help_menu = menu_bar.addMenu("帮助")

        github_action = QtGui.QAction("项目主页 (GitHub)", self)
        github_action.triggered.connect(
            lambda: open_path_in_shell("https://github.com/hamiltonxu650-lang/Slide-Maker")
        )
        help_menu.addAction(github_action)

        open_diag_action = QtGui.QAction("打开诊断日志目录", self)
        open_diag_action.triggered.connect(self._open_diagnostic_dir)
        help_menu.addAction(open_diag_action)

        open_model_action = QtGui.QAction("打开模型目录", self)
        open_model_action.triggered.connect(self._open_model_dir)
        help_menu.addAction(open_model_action)

    @staticmethod
    def _make_focus_slot(method_name):
        """Return a callback that invokes *method_name* on the currently
        focused widget, so Edit menu items work on any active text field."""
        def _slot():
            from PyQt6.QtWidgets import QApplication
            widget = QApplication.focusWidget()
            if widget is not None and hasattr(widget, method_name):
                getattr(widget, method_name)()
        return _slot

    def _menu_switch_page(self, key):
        self.sidebar.select_page(key)
        self._switch_page(key)

    def _menu_toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def changeEvent(self, event):
        super().changeEvent(event)
        if event.type() == QtCore.QEvent.Type.WindowStateChange:
            self._sync_window_chrome()

    def showEvent(self, event):
        super().showEvent(event)
        self._sync_window_chrome()

    def _sync_window_chrome(self):
        maximized = self.isMaximized() or self.isFullScreen()
        margin = 0 if self._use_native_macos_chrome or maximized else 12
        self.outer_layout.setContentsMargins(margin, margin, margin, margin)
        for widget in (self.surface, self.title_bar, self.sidebar):
            if widget is None:
                continue
            widget.setProperty("maximized", maximized)
            widget.setProperty("nativeMacChrome", self._use_native_macos_chrome)
            widget.style().unpolish(widget)
            widget.style().polish(widget)
            widget.update()
        if self.title_bar is not None:
            self.title_bar.update_window_state(maximized)
        self.size_grip.setVisible(not self._use_native_macos_chrome and not maximized)

    def _build_home_page(self):
        page = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        layout.addWidget(scroll, stretch=1)

        content = QtWidgets.QWidget()
        content_layout = QtWidgets.QVBoxLayout(content)
        content_layout.setContentsMargins(40, 32, 34, 36)
        content_layout.setSpacing(20)
        scroll.setWidget(content)

        topbar = QtWidgets.QHBoxLayout()
        topbar.setContentsMargins(0, 0, 0, 0)
        topbar.setSpacing(22)

        welcome = QtWidgets.QHBoxLayout()
        welcome.setSpacing(16)
        app_icon = QtWidgets.QLabel()
        app_icon.setFixedSize(58, 58)
        app_icon.setObjectName("WelcomeIcon")
        icon_path = PROJECT_ROOT / "assets" / "slide_maker_icon.png"
        if icon_path.exists():
            app_icon.setPixmap(sharp_pixmap(icon_path, 58))
        welcome.addWidget(app_icon)

        welcome_text = QtWidgets.QVBoxLayout()
        welcome_text.setSpacing(4)
        title = QtWidgets.QLabel("Welcome, Slide Maker")
        title.setObjectName("DashboardTitle")
        welcome_text.addWidget(title)
        subtitle = QtWidgets.QLabel("本地文档转 PPTX 工作台")
        subtitle.setObjectName("DashboardSubtitle")
        welcome_text.addWidget(subtitle)
        welcome.addLayout(welcome_text)
        topbar.addLayout(welcome)
        topbar.addStretch(1)
        content_layout.addLayout(topbar)

        hero_row = QtWidgets.QHBoxLayout()
        hero_row.setSpacing(20)

        pdf_card = FeatureCard(
            "PDF 转 PPTX",
            "自动拆页、识别文字并重建可编辑幻灯片。",
            PDF_HERO_IMAGE,
            ("#9AF5DD", "#CFE8FF", "#5B93FF"),
            "多页文档",
        )
        pdf_card.clicked.connect(lambda: self.start_conversion_flow("pdf"))
        hero_row.addWidget(pdf_card, stretch=1)

        image_card = FeatureCard(
            "图片转 PPTX",
            "截图、海报和拍摄图片转可编辑幻灯片。",
            IMAGE_HERO_IMAGE,
            ("#E8DEFF", "#FFE8EF", "#FF8F9F"),
            "图片输入",
        )
        image_card.clicked.connect(lambda: self.start_conversion_flow("image"))
        hero_row.addWidget(image_card, stretch=1)
        content_layout.addLayout(hero_row)

        connector = QtWidgets.QFrame()
        connector.setObjectName("ConnectorCard")
        connector_layout = QtWidgets.QHBoxLayout(connector)
        connector_layout.setContentsMargins(24, 12, 18, 12)
        connector_layout.setSpacing(18)

        connector_text = QtWidgets.QVBoxLayout()
        connector_text.setSpacing(3)
        self.selected_file_name_label = QtWidgets.QLabel("还没有选择文件")
        self.selected_file_name_label.setObjectName("ConnectorTitle")
        connector_text.addWidget(self.selected_file_name_label)
        self.selected_file_meta_label = QtWidgets.QLabel("PDF、PNG、JPG、JPEG")
        self.selected_file_meta_label.setObjectName("ConnectorMeta")
        connector_text.addWidget(self.selected_file_meta_label)
        connector_layout.addLayout(connector_text, stretch=1)

        for icon_name in ("file-text", "image", "file-type"):
            icon = QtWidgets.QLabel()
            icon.setObjectName("ConnectorIcon")
            icon.setFixedSize(42, 42)
            icon.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            icon.setPixmap(svg_pixmap(icon_name, "#2F78FF", 20))
            connector_layout.addWidget(icon)

        connector_button = QtWidgets.QPushButton()
        connector_button.setObjectName("ConnectorIconButton")
        connector_button.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        connector_button.setToolTip("选择文件")
        connector_button.setFixedSize(42, 42)
        connector_button.setIcon(svg_icon("file-plus", "#2F78FF", 20))
        connector_button.setIconSize(QtCore.QSize(20, 20))
        connector_button.clicked.connect(self.start_any_conversion_flow)
        connector_layout.addWidget(connector_button)
        content_layout.addWidget(connector)

        self.preference_panel = PreferencePanel()
        content_layout.addWidget(self.preference_panel)

        future_panel = QtWidgets.QFrame()
        future_panel.setObjectName("FuturePanel")
        future_layout = QtWidgets.QHBoxLayout(future_panel)
        future_layout.setContentsMargins(22, 22, 22, 22)
        future_layout.setSpacing(18)

        future_text = QtWidgets.QVBoxLayout()
        future_text.setSpacing(4)
        more_label = QtWidgets.QLabel("正在开发")
        more_label.setObjectName("FutureTitle")
        future_text.addWidget(more_label)
        more_caption = QtWidgets.QLabel("更多输入源会接入同一套 PPTX 生成链路")
        more_caption.setObjectName("SectionCaption")
        more_caption.setWordWrap(True)
        future_text.addWidget(more_caption)
        future_text.addStretch(1)
        future_layout.addLayout(future_text)

        future_grid = QtWidgets.QGridLayout()
        future_grid.setHorizontalSpacing(12)
        future_grid.setVerticalSpacing(12)
        future_layout.addLayout(future_grid, stretch=1)
        placeholders = [
            ("Word", ".docx 文档", "file-type"),
            ("Excel", "表格内容", "table"),
            ("Markdown", "知识稿", "markdown"),
            ("网页", "URL 页面", "globe"),
        ]
        for idx, (name, desc, icon_name) in enumerate(placeholders):
            card = PlaceholderCard(name, desc, icon_name=icon_name)
            card.clicked.connect(self._show_coming_soon)
            future_grid.addWidget(card, 0, idx)
        for col in range(4):
            future_grid.setColumnStretch(col, 1)
        content_layout.addWidget(future_panel)
        content_layout.addStretch(1)

        self.status_panel = StatusPanel()
        self.status_panel.set_demo_mode(self.demo_mode)
        self.status_panel.pickFileRequested.connect(self.start_any_conversion_flow)
        self.status_panel.openResultRequested.connect(self._open_result_file)
        self.status_panel.openFolderRequested.connect(self._open_result_folder)
        self.status_panel.retryRequested.connect(self.retry_last_task)
        self.status_panel.scannerToggled.connect(self._set_scanner_from_status)

        progress_column = QtWidgets.QFrame()
        progress_column.setObjectName("ProgressColumn")
        progress_layout = QtWidgets.QVBoxLayout(progress_column)
        progress_layout.setContentsMargins(40, 40, 28, 36)
        progress_layout.setSpacing(0)
        progress_layout.addWidget(self.status_panel, stretch=1)
        layout.addWidget(progress_column)

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
        scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        root_layout.addWidget(scroll)

        content = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 6, 0)
        layout.setSpacing(16)
        scroll.setWidget(content)

        title = QtWidgets.QLabel("设置")
        title.setObjectName("SectionTitle")
        layout.addWidget(title)

        caption = QtWidgets.QLabel("对各项功能进行个性化配置。")
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

        self.conversion_card = self._create_setting_card("转换", "调整转换过程中的各项参数。")
        conversion_layout = self.conversion_card.layout()
        self.enable_scanner_checkbox = QtWidgets.QCheckBox("启用文档边缘扫描裁正 (适合图片斜拍幻灯片)")
        conversion_layout.addWidget(self.enable_scanner_checkbox)
        self.renderer_combo = QtWidgets.QComboBox()
        self.renderer_combo.addItem("高保真优先", RENDERER_HIGH_FIDELITY)
        self.renderer_combo.addItem("兼容优先", RENDERER_COMPATIBILITY)
        conversion_layout.addLayout(self._form_row("默认渲染模式", self.renderer_combo))
        self.pdf_quality_combo = QtWidgets.QComboBox()
        for dpi in PDF_DPI_CHOICES:
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
        page.setObjectName("AboutPage")
        layout = QtWidgets.QVBoxLayout(page)
        layout.setContentsMargins(48, 48, 48, 48)
        layout.setSpacing(0)

        center = QtWidgets.QFrame()
        center.setObjectName("AboutCenter")
        center_layout = QtWidgets.QVBoxLayout(center)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(16)
        center_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignHCenter)

        app_icon = QtWidgets.QLabel()
        app_icon.setObjectName("AboutIcon")
        app_icon.setFixedSize(86, 86)
        app_icon.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        icon_path = PROJECT_ROOT / "assets" / "slide_maker_icon.png"
        if icon_path.exists():
            app_icon.setPixmap(sharp_pixmap(icon_path, 76))
        center_layout.addWidget(app_icon, alignment=QtCore.Qt.AlignmentFlag.AlignHCenter)

        title = QtWidgets.QLabel("Slide Maker")
        title.setObjectName("AboutTitle")
        title.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        center_layout.addWidget(title)

        subtitle = QtWidgets.QLabel("下一代离线文档转 PPT 工作台")
        subtitle.setObjectName("AboutSubtitle")
        subtitle.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        center_layout.addWidget(subtitle)

        version = QtWidgets.QLabel("版本 0.4.0")
        version.setObjectName("AboutVersionPill")
        version.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        version.setFixedSize(112, 40)
        center_layout.addWidget(version, alignment=QtCore.Qt.AlignmentFlag.AlignHCenter)

        slogan = QtWidgets.QLabel("更智能 · 更高效 · 更专注")
        slogan.setObjectName("AboutSlogan")
        slogan.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        center_layout.addWidget(slogan)

        desc = QtWidgets.QLabel(
            "Slide Maker 是一款离线智能文档转换工具，支持 PDF、图片等格式一键转换为可编辑的 PowerPoint "
            "演示文稿。 核心能力包括 OCR 文字识别、AI 背景修复、文档扫描裁正与画质增强、高保真 PPTX 排版生成。"
        )
        desc.setObjectName("AboutDescription")
        desc.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        desc.setWordWrap(True)
        desc.setMaximumWidth(760)
        center_layout.addWidget(desc)

        credits = QtWidgets.QLabel("Antigravity · Codex · Doctor Eric")
        credits.setObjectName("AboutMeta")
        credits.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        center_layout.addWidget(credits)

        contact = QtWidgets.QLabel("如果遇到任何问题、Bug 或建议，请联系： lewisxu44@outlook.com")
        contact.setObjectName("AboutMeta")
        contact.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        contact.setTextInteractionFlags(QtCore.Qt.TextInteractionFlag.TextSelectableByMouse)
        center_layout.addWidget(contact)

        button_row = QtWidgets.QHBoxLayout()
        button_row.setSpacing(14)
        button_row.setContentsMargins(0, 10, 0, 0)
        button_row.addWidget(
            self._create_about_button("globe", "官方网站", self._show_website_placeholder)
        )
        button_row.addWidget(
            self._create_about_button("book", "帮助文档", lambda: self._open_external_url(GITHUB_PROJECT_URL))
        )
        button_row.addWidget(
            self._create_about_button("message", "反馈建议", lambda: self._open_external_url(GITHUB_PROJECT_URL))
        )
        button_row.addWidget(self._create_about_button("refresh", "检查更新", self._show_update_notice))
        center_layout.addLayout(button_row)

        layout.addStretch(1)
        layout.addWidget(center, alignment=QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.addStretch(2)
        return page

    def _create_about_button(self, icon_name, label, callback):
        button = QtWidgets.QPushButton(label)
        button.setObjectName("AboutActionButton")
        button.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        button.setIcon(svg_icon(icon_name, "#17191F", 20))
        button.setIconSize(QtCore.QSize(20, 20))
        button.setMinimumSize(140, 54)
        button.clicked.connect(callback)
        return button

    def _open_external_url(self, url):
        if not QtGui.QDesktopServices.openUrl(QtCore.QUrl(url)):
            QtWidgets.QMessageBox.information(self, APP_BRAND, "暂时无法打开链接，请稍后再试。")

    def _show_website_placeholder(self):
        QtWidgets.QMessageBox.information(
            self,
            APP_BRAND,
            "官方网站暂未开放。\n这个入口会作为后续官网发布后的占位入口保留。",
        )

    def _show_update_notice(self):
        dialog = QtWidgets.QDialog(self)
        dialog.setObjectName("UpdateDialog")
        dialog.setWindowTitle("检查更新")
        dialog.setModal(True)
        dialog.setFixedWidth(540)
        dialog.setWindowFlags(QtCore.Qt.WindowType.Dialog | QtCore.Qt.WindowType.FramelessWindowHint)
        dialog.setAttribute(QtCore.Qt.WidgetAttribute.WA_StyledBackground, True)
        dialog.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground, True)

        layout = QtWidgets.QVBoxLayout(dialog)
        layout.setContentsMargins(12, 12, 12, 12)

        card = QtWidgets.QFrame()
        card.setObjectName("UpdateDialogCard")
        card_layout = QtWidgets.QVBoxLayout(card)
        card_layout.setContentsMargins(28, 26, 28, 24)
        card_layout.setSpacing(14)
        layout.addWidget(card)

        title = QtWidgets.QLabel("当前已是最新版本")
        title.setObjectName("UpdateDialogTitle")
        title.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(title)

        version = QtWidgets.QLabel("Slide Maker 0.4.0")
        version.setObjectName("UpdateDialogVersion")
        version.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(version, alignment=QtCore.Qt.AlignmentFlag.AlignHCenter)

        body = QtWidgets.QLabel(
            "这是目前发布的最终版本，暂不提供自动更新。\n\n"
            "但如果你有任何使用上的想法或改进建议，非常欢迎通过邮件与我们交流。"
            "你的反馈对我们很重要。"
        )
        body.setObjectName("UpdateDialogBody")
        body.setWordWrap(True)
        body.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(body)

        email = QtWidgets.QLabel("✉ lewisxu44@outlook.com")
        email.setObjectName("UpdateDialogEmail")
        email.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        email.setTextInteractionFlags(QtCore.Qt.TextInteractionFlag.TextSelectableByMouse)
        card_layout.addWidget(email)

        help_button = QtWidgets.QPushButton("跳转到 GitHub 主页")
        help_button.setObjectName("UpdateDialogHelpButton")
        help_button.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        help_button.setMinimumHeight(46)
        help_button.setIcon(svg_icon("book", "#17191F", 18))
        help_button.setIconSize(QtCore.QSize(18, 18))
        help_button.clicked.connect(lambda: self._open_external_url(GITHUB_PROJECT_URL))
        card_layout.addWidget(help_button)
        card_layout.addSpacing(8)

        close_button = QtWidgets.QPushButton("知道了")
        close_button.setObjectName("UpdateDialogButton")
        close_button.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        close_button.setFixedSize(128, 42)
        close_button.clicked.connect(dialog.accept)
        card_layout.addWidget(close_button, alignment=QtCore.Qt.AlignmentFlag.AlignHCenter)

        dialog.exec()

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
            self.enable_scanner_checkbox,
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
            self.enable_scanner_checkbox.setChecked(settings.enable_document_scanner)
            self.renderer_combo.setCurrentIndex(max(0, self.renderer_combo.findData(settings.preferred_renderer)))
            self.pdf_quality_combo.setCurrentIndex(max(0, self.pdf_quality_combo.findData(settings.pdf_quality_dpi)))
            self.cleanup_combo.setCurrentIndex(max(0, self.cleanup_combo.findData(settings.background_cleanup)))
            self.text_mode_combo.setCurrentIndex(max(0, self.text_mode_combo.findData(settings.text_mode)))
            self.diagnostics_checkbox.setChecked(settings.diagnostic_logs)
            if hasattr(self, "status_panel"):
                self.status_panel.set_settings(settings)
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
            enable_document_scanner=self.enable_scanner_checkbox.isChecked(),
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
        if hasattr(self, "status_panel"):
            self.status_panel.set_settings(self.app_settings)
        self.output_suffix_edit.setText(self.app_settings.output_suffix)
        if not self.app_settings.remember_recent_tasks:
            self.recent_tasks = []
            clear_recent_tasks()
            self._refresh_recent_list()
        self._refresh_runtime_labels()

    def _set_scanner_from_status(self, enabled):
        if self._syncing_settings:
            return
        self.app_settings.enable_document_scanner = bool(enabled)
        save_app_settings(self.app_settings)
        if hasattr(self, "enable_scanner_checkbox"):
            self._syncing_settings = True
            try:
                self.enable_scanner_checkbox.setChecked(bool(enabled))
            finally:
                self._syncing_settings = False
        if hasattr(self, "status_panel"):
            self.status_panel.set_settings(self.app_settings)

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
        self.status_panel.show_notice(f"{title} \u6a21\u5757\u5373\u5c06\u63a8\u51fa\uff0c\u656c\u8bf7\u671f\u5f85\u3002")
        self.sidebar.select_page("home")

    def _supported_image_suffixes(self) -> set[str]:
        if sys.platform == "darwin":
            return COMMON_IMAGE_SUFFIXES | MAC_ONLY_IMAGE_SUFFIXES
        return set(COMMON_IMAGE_SUFFIXES)

    def _build_file_filter(self, input_kind):
        if input_kind == "pdf":
            return "PDF 文件 (*.pdf)"
        suffixes = " ".join(f"*{suffix}" for suffix in sorted(self._supported_image_suffixes()))
        return f"图片文件 ({suffixes})"

    def _detect_input_kind(self, input_path: str) -> str | None:
        suffix = Path(input_path).suffix.lower()
        if suffix == ".pdf":
            return "pdf"
        if suffix in self._supported_image_suffixes():
            return "image"
        return None

    def _update_selected_file_display(self, input_path: str, input_kind: str):
        if not hasattr(self, "selected_file_name_label"):
            return
        file_path = Path(input_path)
        self.selected_file_name_label.setText(file_path.name)
        meta = "PDF 转 PPTX" if input_kind == "pdf" else "图片转 PPTX"
        self.selected_file_meta_label.setText(f"{meta} · {file_path.suffix.upper().lstrip('.')}")

    def _collect_task_preferences(self) -> TaskPreferences:
        preferences = self.preference_panel.get_preferences()
        status_note = self.status_panel.get_note() if hasattr(self, "status_panel") else ""
        if status_note:
            preferences = TaskPreferences(focus=preferences.focus, note=status_note).with_mapped_tags()
        return preferences

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
            self.status_panel.show_notice(f"{label} 功能在演示模式下不可用。")
            return

        input_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "选择输入文件",
            str(Path.home()),
            self._build_file_filter(input_kind),
        )
        if not input_path:
            return

        self._start_selected_input(input_kind, input_path)

    def start_any_conversion_flow(self):
        if self.worker and self.worker.isRunning():
            self.status_panel.show_notice("当前已有任务在执行，请等待完成后再发起新任务。")
            return

        if self.demo_mode:
            self.status_panel.show_notice("选择文件功能在演示模式下不可用。")
            return

        input_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "选择输入文件",
            str(Path.home()),
            f"PDF / 图片文件 (*.pdf {' '.join(f'*{suffix}' for suffix in sorted(self._supported_image_suffixes()))})",
        )
        if not input_path:
            return

        input_kind = self._detect_input_kind(input_path)
        if not input_kind:
            image_labels = ", ".join(suffix.upper().lstrip(".") for suffix in sorted(self._supported_image_suffixes()))
            self.status_panel.show_notice(f"请选择 PDF 或 {image_labels} 文件。")
            return
        self._start_selected_input(input_kind, input_path)

    def _start_selected_input(self, input_kind, input_path):
        self._update_selected_file_display(input_path, input_kind)

        if getattr(self.app_settings, "enable_document_scanner", False) and input_kind == "image":
            import cv2
            import numpy as np
            import subprocess
            from ui.scanner_dialog import ScannerDialog
            from scanner_engine import detect_document_corners, four_point_transform, enhance_scanned_document

            actual_input = input_path
            # Auto-convert HEIC to JPG only on macOS where sips is available.
            if sys.platform == "darwin" and input_path.lower().endswith((".heic", ".heif")):
                import tempfile
                fd, converted_path = tempfile.mkstemp(suffix=".jpg", prefix="slide-maker-heic-")
                os.close(fd)
                try:
                    subprocess.run(
                        ["sips", "-s", "format", "jpeg", input_path, "--out", converted_path],
                        check=True, capture_output=True,
                    )
                    actual_input = converted_path
                except Exception:
                    pass  # fallback to trying cv2 directly

            img_bgr = cv2.imdecode(np.fromfile(actual_input, dtype=np.uint8), cv2.IMREAD_COLOR)
            if img_bgr is not None:
                initial_pts = detect_document_corners(img_bgr)
                dialog = ScannerDialog(img_bgr, initial_pts, self)
                if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
                    final_pts = dialog.get_points()
                    warped = four_point_transform(img_bgr, final_pts)
                    # Apply CamScanner-style enhancement
                    enhanced = enhance_scanned_document(warped, mode="color_enhance")

                    import tempfile
                    fd, tmp_path = tempfile.mkstemp(suffix=".png", prefix="slide-maker-scan-")
                    os.close(fd)
                    cv2.imencode(".png", enhanced)[1].tofile(tmp_path)
                    input_path = tmp_path

                    original_scan = self.app_settings.enable_document_scanner
                    self.app_settings.enable_document_scanner = False
                    output_path = self._choose_output_path(input_path)

                    if output_path:
                        preferences = self._collect_task_preferences()
                        self._launch_worker(input_path, output_path, input_kind, preferences)

                    self.app_settings.enable_document_scanner = original_scan
                    return

        output_path = self._choose_output_path(input_path)
        if not output_path:
            return

        preferences = self._collect_task_preferences()
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
