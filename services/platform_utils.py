from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys


def is_windows() -> bool:
    return os.name == "nt"


def is_macos() -> bool:
    return sys.platform == "darwin"


def preferred_ui_font_family() -> str:
    if is_windows():
        return "Microsoft YaHei UI"
    if is_macos():
        return "PingFang SC"
    return "Noto Sans CJK SC"


def open_path_in_shell(path: str | Path) -> bool:
    target = str(Path(path))
    if not target:
        return False

    try:
        if is_windows():
            os.startfile(target)
            return True
        if is_macos():
            subprocess.Popen(["open", target])
            return True
        subprocess.Popen(["xdg-open", target])
        return True
    except Exception:
        return False


def desktop_dir() -> Path:
    return Path.home() / "Desktop"
