import argparse
import json
from pathlib import Path
import traceback

from services.app_models import AppSettings, TaskPreferences, app_data_root
from services.conversion_service import run_conversion


PROGRESS_PREFIX = "GUI_PROGRESS"
LOG_PREFIX = "GUI_LOG"
RESULT_PREFIX = "GUI_RESULT"
ERROR_PREFIX = "GUI_ERROR"
_CHANNEL_FILE = None


def configure_channel_file(path):
    global _CHANNEL_FILE
    _CHANNEL_FILE = Path(path) if path else None


def emit(prefix, payload):
    line = f"{prefix}|{json.dumps(payload, ensure_ascii=False)}"
    if _CHANNEL_FILE:
        _CHANNEL_FILE.parent.mkdir(parents=True, exist_ok=True)
        with _CHANNEL_FILE.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")
    else:
        print(line, flush=True)


def progress_cb(stage, percent, detail):
    emit(
        PROGRESS_PREFIX,
        {
            "stage": stage,
            "percent": percent,
            "detail": detail,
        },
    )


def log_cb(message):
    emit(LOG_PREFIX, {"message": message})


def write_worker_crash_log(message, trace):
    try:
        log_dir = app_data_root() / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        crash_log = log_dir / "worker-crash.log"
        crash_log.write_text(f"{message}\n\n{trace}", encoding="utf-8")
    except Exception:
        pass


def run_hidden(input_path, output_path, input_kind, settings_json="{}", preferences_json="{}", channel_file=None):
    try:
        configure_channel_file(channel_file)
        settings = AppSettings.from_dict(json.loads(settings_json))
        preferences = TaskPreferences.from_dict(json.loads(preferences_json))
        result = run_conversion(
            input_path,
            output_path=output_path,
            input_kind=input_kind,
            auto_open=False,
            progress_cb=progress_cb,
            log_cb=log_cb,
            settings=settings,
            preferences=preferences,
        )
    except Exception as exc:
        trace = traceback.format_exc()
        write_worker_crash_log(str(exc), trace)
        emit(
            ERROR_PREFIX,
            {
                "message": str(exc),
                "traceback": trace,
            },
        )
        return 1

    emit(RESULT_PREFIX, result)
    return 0


def main():
    parser = argparse.ArgumentParser(description="Hidden conversion entrypoint for the desktop GUI")
    parser.add_argument("--input-path", required=True)
    parser.add_argument("--output-path", required=True)
    parser.add_argument("--input-kind", required=True, choices=("pdf", "image"))
    parser.add_argument("--settings-json", default="{}")
    parser.add_argument("--preferences-json", default="{}")
    parser.add_argument("--channel-file", default=None)
    args = parser.parse_args()
    return run_hidden(
        args.input_path,
        args.output_path,
        args.input_kind,
        settings_json=args.settings_json,
        preferences_json=args.preferences_json,
        channel_file=args.channel_file,
    )


if __name__ == "__main__":
    raise SystemExit(main())
