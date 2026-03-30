import argparse
from datetime import datetime
from pathlib import Path
import sys
import traceback

from services.app_models import APP_BRAND, app_data_root
from services.platform_utils import preferred_ui_font_family
from services.runtime_env import configure_runtime_dll_search_paths, find_app_icon, preload_runtime_libraries


def build_parser():
    parser = argparse.ArgumentParser(description=f"{APP_BRAND} Desktop UI")
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Preview the UI only without running real conversions.",
    )
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--input-path", default=None, help=argparse.SUPPRESS)
    parser.add_argument("--output-path", default=None, help=argparse.SUPPRESS)
    parser.add_argument("--input-kind", choices=("pdf", "image"), default=None, help=argparse.SUPPRESS)
    parser.add_argument("--settings-json", default="{}", help=argparse.SUPPRESS)
    parser.add_argument("--preferences-json", default="{}", help=argparse.SUPPRESS)
    parser.add_argument("--channel-file", default=None, help=argparse.SUPPRESS)
    parser.add_argument("--close-after-ms", type=int, default=None, help=argparse.SUPPRESS)
    return parser


def _append_gui_log(message: str) -> None:
    try:
        log_path = app_data_root() / "logs" / "ui-launch.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("a", encoding="utf-8") as handle:
            handle.write(f"[{datetime.now().isoformat(timespec='seconds')}] {message.rstrip()}\n")
    except Exception:
        pass


def main():
    args = build_parser().parse_args()
    dll_dirs = configure_runtime_dll_search_paths()
    preload_info = preload_runtime_libraries()

    if args.worker:
        bootstrap_log = app_data_root() / "logs" / "worker-bootstrap.log"
        try:
            bootstrap_log.parent.mkdir(parents=True, exist_ok=True)
            bootstrap_log.write_text(
                "argv="
                + repr(sys.argv)
                + "\n"
                + "dll_dirs="
                + repr(dll_dirs)
                + "\n"
                + "preloaded="
                + repr(preload_info.get("loaded", []))
                + "\n"
                + "preload_failed="
                + repr(preload_info.get("failed", []))
                + "\n",
                encoding="utf-8",
            )
        except Exception:
            bootstrap_log = None

        try:
            from gui_conversion_runner import run_hidden

            return run_hidden(
                args.input_path,
                args.output_path,
                args.input_kind,
                settings_json=args.settings_json,
                preferences_json=args.preferences_json,
                channel_file=args.channel_file,
            )
        except Exception as exc:
            if bootstrap_log is not None:
                with bootstrap_log.open("a", encoding="utf-8") as handle:
                    handle.write("\n" + traceback.format_exc())
            if args.channel_file:
                import json

                with Path(args.channel_file).open("a", encoding="utf-8") as handle:
                    handle.write(
                        "GUI_ERROR|"
                        + json.dumps(
                            {
                                "message": str(exc),
                                "traceback": traceback.format_exc(),
                            },
                            ensure_ascii=False,
                        )
                        + "\n"
                    )
            raise

    try:
        from PyQt6 import QtCore, QtGui, QtWidgets

        from ui.main_window import MainWindow
        from ui.theme import apply_theme

        app = QtWidgets.QApplication(sys.argv)
        app.setApplicationName(APP_BRAND)
        app.setQuitOnLastWindowClosed(True)
        app.setFont(QtGui.QFont(preferred_ui_font_family(), 10))
        icon_path = find_app_icon()
        if icon_path:
            app.setWindowIcon(QtGui.QIcon(str(icon_path)))
        apply_theme(app)

        window = MainWindow(demo_mode=args.demo)
        window.show()

        if args.close_after_ms:
            QtCore.QTimer.singleShot(args.close_after_ms, app.quit)

        exit_code = app.exec()
        if exit_code != 0:
            _append_gui_log(f"UI exited with code {exit_code}; argv={sys.argv!r}")
        return exit_code
    except Exception:
        _append_gui_log("Unhandled UI exception:\n" + traceback.format_exc())
        raise


if __name__ == "__main__":
    sys.exit(main())
