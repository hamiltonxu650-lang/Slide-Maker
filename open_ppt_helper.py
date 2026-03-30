import ctypes
import os
import sys

from services.app_models import APP_BRAND
from services.platform_utils import is_windows, open_path_in_shell


def ask_to_open(file_path):
    if not os.path.exists(file_path):
        print(f"Error: File not found at {file_path}")
        return

    if not is_windows():
        print(f"{APP_BRAND}: generated {file_path}")
        if not open_path_in_shell(file_path):
            print("Open skipped because the platform shell could not launch the file.")
        return

    title = f"{APP_BRAND} 转换完成"
    message = f"已成功生成 PPTX，是否立即打开查看？\n\n文件：{os.path.basename(file_path)}"
    response = ctypes.windll.user32.MessageBoxW(0, message, title, 0x04 | 0x20 | 0x1000)

    if response == 6:
        print(f"Opening {file_path}...")
        open_path_in_shell(file_path)
    else:
        print("User chose not to open the file.")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        target_file = os.path.abspath(sys.argv[1])
        ask_to_open(target_file)
    else:
        print("Usage: python open_ppt_helper.py <path_to_pptx>")
