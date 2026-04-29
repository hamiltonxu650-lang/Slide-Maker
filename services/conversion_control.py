from __future__ import annotations

import json
import time
from pathlib import Path


ACTION_CANCEL = "cancel"
ACTION_PAUSE = "pause"
ACTION_RUN = "run"


class ConversionCancelled(RuntimeError):
    pass


class ConversionController:
    def __init__(self, control_file: str | None = None, progress_cb=None) -> None:
        self.control_file = Path(control_file) if control_file else None
        self.progress_cb = progress_cb
        self._pause_announced = False

    def _read_action(self) -> str:
        if not self.control_file or not self.control_file.exists():
            return ACTION_RUN
        try:
            payload = json.loads(self.control_file.read_text(encoding="utf-8") or "{}")
        except (OSError, json.JSONDecodeError):
            return ACTION_RUN
        return str(payload.get("action") or ACTION_RUN).strip().lower()

    def check(self, stage: str = "转换中", percent: int = 0, detail: str = "") -> None:
        action = self._read_action()
        if action == ACTION_CANCEL:
            raise ConversionCancelled("转换已取消。")

        if action != ACTION_PAUSE:
            self._pause_announced = False
            return

        while action == ACTION_PAUSE:
            if not self._pause_announced and self.progress_cb:
                self.progress_cb(stage, percent, detail or "转换已暂停，点击继续后会从当前安全点恢复。")
            self._pause_announced = True
            time.sleep(0.25)
            action = self._read_action()
            if action == ACTION_CANCEL:
                raise ConversionCancelled("转换已取消。")

        self._pause_announced = False


def write_control_action(control_file: str | Path, action: str) -> None:
    path = Path(control_file)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"action": action, "updated_at": time.time()}, ensure_ascii=False),
        encoding="utf-8",
    )
