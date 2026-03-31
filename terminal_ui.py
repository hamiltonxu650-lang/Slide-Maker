from __future__ import annotations

import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass

from services.app_models import (
    APP_BRAND,
    BACKGROUND_CHOICES,
    BACKGROUND_STANDARD,
    BACKGROUND_STRONG,
    OCR_MODEL_DOWNLOADS,
    PREFERENCE_CHOICES,
    PREFERENCE_CLARITY,
    PREFERENCE_CLEANUP,
    PREFERENCE_LAYOUT,
    PREFERENCE_SPEED,
    PDF_DPI_CHOICES,
    RENDERER_CHOICES,
    RENDERER_COMPATIBILITY,
    RENDERER_HIGH_FIDELITY,
    TEXT_MODE_CHOICES,
    TEXT_MODE_CLEAR,
    TEXT_MODE_FAITHFUL,
    AppSettings,
    TaskPreferences,
    app_data_root,
    describe_lama_model_setup,
    describe_ocr_model_setup,
    lama_model_slot,
    ocr_model_slot_dir,
    sanitize_suffix,
)
from services.conversion_service import infer_input_kind, run_conversion
from services.platform_utils import open_path_in_shell
from services.runtime_env import describe_runtime_environment, detect_project_root


PROJECT_ROOT = Path(__file__).resolve().parent
STATE_PATH = app_data_root(PROJECT_ROOT) / "config" / "terminal_ui.json"

RENDERER_LABELS = {
    RENDERER_HIGH_FIDELITY: "高保真优先",
    RENDERER_COMPATIBILITY: "兼容优先",
}
BACKGROUND_LABELS = {
    BACKGROUND_STANDARD: "标准",
    BACKGROUND_STRONG: "强力",
}
TEXT_MODE_LABELS = {
    TEXT_MODE_FAITHFUL: "忠实还原",
    TEXT_MODE_CLEAR: "更清晰",
}
FOCUS_LABELS = {
    PREFERENCE_LAYOUT: "默认 / 排版优先",
    PREFERENCE_CLARITY: "优先文字清晰",
    PREFERENCE_CLEANUP: "优先背景干净",
    PREFERENCE_SPEED: "优先转换速度",
}


@dataclass
class TerminalUIState:
    lama_model_path: str = ""
    ocr_det_model_path: str = ""
    ocr_cls_model_path: str = ""
    ocr_rec_model_path: str = ""
    preferred_renderer: str = RENDERER_HIGH_FIDELITY
    pdf_quality_dpi: int = 200
    background_cleanup: str = BACKGROUND_STANDARD
    text_mode: str = TEXT_MODE_FAITHFUL
    focus: str = PREFERENCE_LAYOUT
    note: str = ""
    auto_open_result: bool = False
    output_dir: str = ""
    output_suffix: str = "_Result"
    diagnostic_logs: bool = True
    last_input_path: str = ""
    first_run_complete: bool = False

    @classmethod
    def from_dict(cls, data: dict | None) -> "TerminalUIState":
        data = dict(data or {})
        state = cls()
        for key in state.to_dict():
            if key in data:
                setattr(state, key, data[key])

        if state.preferred_renderer not in RENDERER_CHOICES:
            state.preferred_renderer = RENDERER_HIGH_FIDELITY
        if int(state.pdf_quality_dpi) not in PDF_DPI_CHOICES:
            state.pdf_quality_dpi = 200
        state.pdf_quality_dpi = int(state.pdf_quality_dpi)
        if state.background_cleanup not in BACKGROUND_CHOICES:
            state.background_cleanup = BACKGROUND_STANDARD
        if state.text_mode not in TEXT_MODE_CHOICES:
            state.text_mode = TEXT_MODE_FAITHFUL
        if state.focus not in PREFERENCE_CHOICES:
            state.focus = PREFERENCE_LAYOUT
        state.note = str(state.note or "").strip()
        state.output_dir = str(state.output_dir or "").strip()
        state.output_suffix = sanitize_suffix(state.output_suffix or "_Result")
        state.last_input_path = str(state.last_input_path or "").strip()
        return state

    def to_dict(self) -> dict:
        return asdict(self)


def load_state() -> TerminalUIState:
    if not STATE_PATH.exists():
        return TerminalUIState()
    try:
        data = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return TerminalUIState()
    return TerminalUIState.from_dict(data)


def save_state(state: TerminalUIState) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")


def apply_model_env(state: TerminalUIState) -> None:
    mapping = {
        "SLIDE_MAKER_LAMA_MODEL": state.lama_model_path,
        "SLIDE_MAKER_OCR_DET_MODEL": state.ocr_det_model_path,
        "SLIDE_MAKER_OCR_CLS_MODEL": state.ocr_cls_model_path,
        "SLIDE_MAKER_OCR_REC_MODEL": state.ocr_rec_model_path,
    }
    for env_var, value in mapping.items():
        cleaned = str(value or "").strip()
        if cleaned:
            os.environ[env_var] = str(Path(cleaned).expanduser())
        else:
            os.environ.pop(env_var, None)


def reset_cached_runtimes() -> None:
    try:
        from inpainting_engine import reset_lama_runtime

        reset_lama_runtime()
    except Exception:
        pass

    try:
        from ocr_engine import reset_ocr_runtime

        reset_ocr_runtime()
    except Exception:
        pass


def clear_screen() -> None:
    if sys.stdout.isatty():
        os.system("cls" if os.name == "nt" else "clear")


def pause(message: str = "按 Enter 继续...") -> None:
    try:
        input(message)
    except EOFError:
        pass


def ask_text(prompt: str, default: str | None = None) -> str:
    suffix = f" [{default}]" if default else ""
    raw = input(f"{prompt}{suffix}: ").strip()
    if not raw and default is not None:
        return str(default)
    return raw.strip().strip('"').strip("'")


def ask_yes_no(prompt: str, default: bool = True) -> bool:
    hint = "Y/n" if default else "y/N"
    while True:
        raw = input(f"{prompt} [{hint}]: ").strip().lower()
        if not raw:
            return default
        if raw in {"y", "yes", "1"}:
            return True
        if raw in {"n", "no", "0"}:
            return False
        print("请输入 y 或 n。")


def ask_menu_choice(title: str, options: list[tuple[str, str]], default: str | None = None) -> str:
    print(title)
    for key, label in options:
        marker = " (默认)" if default is not None and key == default else ""
        print(f"  {key}. {label}{marker}")
    valid = {key for key, _ in options}
    while True:
        raw = input("选择: ").strip()
        if not raw and default is not None:
            return default
        if raw in valid:
            return raw
        print("请输入列表中的编号。")


def ask_existing_path(prompt: str, default: str | None = None, expect_dir: bool | None = None) -> Path:
    while True:
        value = ask_text(prompt, default=default)
        path = Path(value).expanduser()
        if not path.exists():
            print(f"路径不存在: {path}")
            continue
        if expect_dir is True and not path.is_dir():
            print(f"需要目录路径: {path}")
            continue
        if expect_dir is False and not path.is_file():
            print(f"需要文件路径: {path}")
            continue
        try:
            return path.resolve()
        except OSError:
            return path


def print_header(title: str) -> None:
    clear_screen()
    print(f"{APP_BRAND} Terminal UI")
    print(title)
    print("=" * 72)
    print(f"Project: {PROJECT_ROOT}")
    print()


def describe_active_status(state: TerminalUIState) -> tuple[dict, dict, dict]:
    apply_model_env(state)
    runtime_info = describe_runtime_environment()
    lama_info = describe_lama_model_setup(PROJECT_ROOT)
    ocr_info = describe_ocr_model_setup(PROJECT_ROOT)
    return runtime_info, lama_info, ocr_info


def show_environment_status(state: TerminalUIState) -> None:
    runtime_info, lama_info, ocr_info = describe_active_status(state)
    print_header("环境状态")
    print(f"OS: {platform.system()} {platform.release()}")
    print(f"Python: {sys.executable}")
    print(f"Node: {runtime_info['node_path'] or '未找到'}")
    print(f"高保真渲染: {'可用' if runtime_info['high_fidelity_available'] else '不可用'}")
    print(f"日志目录: {runtime_info['log_dir']}")
    print()

    print("LaMa 模型")
    print(f"  状态: {lama_info['message']}")
    print(f"  预留槽位: {lama_info['slot_path']}")
    if lama_info.get("model_path"):
        print(f"  当前路径: {lama_info['model_path']}")
    print()

    print("OCR 模型")
    print(f"  状态: {ocr_info['message']}")
    print(f"  预留槽位目录: {ocr_info['slot_dir']}")
    for model_kind in ("det", "cls", "rec"):
        info = ocr_info["models"][model_kind]
        current_path = info["path"] or "(使用内置模型)"
        print(f"  {model_kind}: source={info['source']} path={current_path}")
    print()

    print("终端 UI 默认设置")
    print(f"  渲染模式: {RENDERER_LABELS[state.preferred_renderer]}")
    print(f"  PDF DPI: {state.pdf_quality_dpi}")
    print(f"  背景净化: {BACKGROUND_LABELS[state.background_cleanup]}")
    print(f"  文字模式: {TEXT_MODE_LABELS[state.text_mode]}")
    print(f"  偏好焦点: {FOCUS_LABELS[state.focus]}")
    print(f"  自动打开结果: {'是' if state.auto_open_result else '否'}")
    print(f"  默认输出目录: {state.output_dir or '(跟随输入目录)'}")
    print()
    pause()


def show_ocr_download_links() -> None:
    print_header("OCR 官方下载地址")
    for model_kind, info in OCR_MODEL_DOWNLOADS.items():
        print(f"{model_kind}:")
        print(f"  文件名: {info['filename']}")
        print(f"  URL: {info['url']}")
        print(f"  SHA256: {info['sha256']}")
        print()
    pause()


def copy_file_to_slot(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def copy_lama_model_to_slot() -> None:
    print_header("复制 LaMa 模型到预留槽位")
    source = ask_existing_path("请输入已下载的 big-lama.pt 路径", expect_dir=False)
    destination = lama_model_slot(PROJECT_ROOT)
    copy_file_to_slot(source, destination)
    reset_cached_runtimes()
    print(f"已复制到: {destination}")
    pause()


def configure_custom_lama_path(state: TerminalUIState) -> None:
    print_header("配置自定义 LaMa 模型路径")
    source = ask_existing_path("请输入 big-lama.pt 路径", default=state.lama_model_path or None, expect_dir=False)
    state.lama_model_path = str(source)
    save_state(state)
    reset_cached_runtimes()
    print("已保存。终端 UI 后续会优先使用这个路径。")
    pause()


def clear_custom_lama_path(state: TerminalUIState) -> None:
    state.lama_model_path = ""
    save_state(state)
    reset_cached_runtimes()
    print("已清除自定义 LaMa 路径。")
    pause()


def run_ocr_download() -> None:
    print_header("下载 OCR 官方模型")
    command = [sys.executable, str(PROJECT_ROOT / "scripts" / "download_ocr_models.py")]
    print("即将执行:")
    print("  " + " ".join(command))
    print()
    if not ask_yes_no("继续下载到 OCR 预留槽位吗？", default=True):
        return
    subprocess.run(command, cwd=str(PROJECT_ROOT), check=False)
    reset_cached_runtimes()
    pause()


def copy_ocr_models_to_slot() -> None:
    print_header("复制 OCR 模型到预留槽位")
    source_dir = ask_existing_path("请输入包含 3 个 ONNX 文件的目录", expect_dir=True)
    target_dir = ocr_model_slot_dir(PROJECT_ROOT)
    missing = []
    for info in OCR_MODEL_DOWNLOADS.values():
        src = source_dir / info["filename"]
        if not src.exists():
            missing.append(str(src))
    if missing:
        print("缺少以下文件:")
        for item in missing:
            print(f"  - {item}")
        pause()
        return

    for info in OCR_MODEL_DOWNLOADS.values():
        copy_file_to_slot(source_dir / info["filename"], target_dir / info["filename"])
    reset_cached_runtimes()
    print(f"已复制到: {target_dir}")
    pause()


def configure_custom_ocr_paths(state: TerminalUIState) -> None:
    print_header("配置自定义 OCR 模型路径")
    det = ask_existing_path(
        "det 模型路径",
        default=state.ocr_det_model_path or None,
        expect_dir=False,
    )
    cls = ask_existing_path(
        "cls 模型路径",
        default=state.ocr_cls_model_path or None,
        expect_dir=False,
    )
    rec = ask_existing_path(
        "rec 模型路径",
        default=state.ocr_rec_model_path or None,
        expect_dir=False,
    )
    state.ocr_det_model_path = str(det)
    state.ocr_cls_model_path = str(cls)
    state.ocr_rec_model_path = str(rec)
    save_state(state)
    reset_cached_runtimes()
    print("已保存。终端 UI 后续会优先使用这 3 个自定义 OCR 模型路径。")
    pause()


def clear_custom_ocr_paths(state: TerminalUIState) -> None:
    state.ocr_det_model_path = ""
    state.ocr_cls_model_path = ""
    state.ocr_rec_model_path = ""
    save_state(state)
    reset_cached_runtimes()
    print("已清除自定义 OCR 路径。")
    pause()


def open_common_model_dirs() -> None:
    print_header("打开模型目录")
    paths = {
        "1": ("LaMa 槽位目录", lama_model_slot(PROJECT_ROOT).parent),
        "2": ("OCR 槽位目录", ocr_model_slot_dir(PROJECT_ROOT)),
    }
    choice = ask_menu_choice(
        "请选择要打开的目录",
        [(key, label) for key, (label, _) in paths.items()] + [("0", "返回")],
        default="0",
    )
    if choice == "0":
        return
    label, path = paths[choice]
    path.mkdir(parents=True, exist_ok=True)
    if open_path_in_shell(path):
        print(f"已尝试打开: {label} -> {path}")
    else:
        print(f"无法直接打开，请手动查看: {path}")
    pause()


def configure_models_menu(state: TerminalUIState) -> None:
    while True:
        runtime_info, lama_info, ocr_info = describe_active_status(state)
        print_header("模型配置")
        print(f"LaMa: {lama_info['message']}")
        print(f"OCR: {ocr_info['message']}")
        print()
        choice = ask_menu_choice(
            "请选择操作",
            [
                ("1", "查看当前模型状态"),
                ("2", "复制 LaMa 模型到预留槽位"),
                ("3", "设置自定义 LaMa 模型路径"),
                ("4", "清除自定义 LaMa 路径"),
                ("5", "下载 OCR 官方模型到预留槽位"),
                ("6", "从本地目录复制 OCR 模型到预留槽位"),
                ("7", "设置自定义 OCR 模型路径"),
                ("8", "清除自定义 OCR 路径"),
                ("9", "查看 OCR 官方下载地址"),
                ("10", "打开模型目录"),
                ("0", "返回主菜单"),
            ],
            default="0",
        )
        if choice == "0":
            return
        if choice == "1":
            show_environment_status(state)
        elif choice == "2":
            copy_lama_model_to_slot()
        elif choice == "3":
            configure_custom_lama_path(state)
        elif choice == "4":
            clear_custom_lama_path(state)
        elif choice == "5":
            run_ocr_download()
        elif choice == "6":
            copy_ocr_models_to_slot()
        elif choice == "7":
            configure_custom_ocr_paths(state)
        elif choice == "8":
            clear_custom_ocr_paths(state)
        elif choice == "9":
            show_ocr_download_links()
        elif choice == "10":
            open_common_model_dirs()


def configure_defaults_menu(state: TerminalUIState) -> None:
    while True:
        print_header("转换默认设置")
        print(f"1. 渲染模式: {RENDERER_LABELS[state.preferred_renderer]}")
        print(f"2. PDF DPI: {state.pdf_quality_dpi}")
        print(f"3. 背景净化: {BACKGROUND_LABELS[state.background_cleanup]}")
        print(f"4. 文字模式: {TEXT_MODE_LABELS[state.text_mode]}")
        print(f"5. 偏好焦点: {FOCUS_LABELS[state.focus]}")
        print(f"6. 补充备注: {state.note or '(空)'}")
        print(f"7. 自动打开结果: {'是' if state.auto_open_result else '否'}")
        print(f"8. 默认输出目录: {state.output_dir or '(跟随输入目录)'}")
        print(f"9. 默认文件名后缀: {state.output_suffix}")
        print(f"10. 诊断日志: {'开启' if state.diagnostic_logs else '关闭'}")
        print("0. 返回主菜单")
        print()
        choice = input("选择: ").strip()
        if choice == "0":
            save_state(state)
            return
        if choice == "1":
            selected = ask_menu_choice(
                "选择渲染模式",
                [("1", RENDERER_LABELS[RENDERER_HIGH_FIDELITY]), ("2", RENDERER_LABELS[RENDERER_COMPATIBILITY])],
                default="1" if state.preferred_renderer == RENDERER_HIGH_FIDELITY else "2",
            )
            state.preferred_renderer = RENDERER_HIGH_FIDELITY if selected == "1" else RENDERER_COMPATIBILITY
        elif choice == "2":
            selected = ask_menu_choice(
                "选择 PDF DPI",
                [(str(index + 1), f"{dpi} DPI") for index, dpi in enumerate(PDF_DPI_CHOICES)],
                default=str(PDF_DPI_CHOICES.index(state.pdf_quality_dpi) + 1),
            )
            state.pdf_quality_dpi = PDF_DPI_CHOICES[int(selected) - 1]
        elif choice == "3":
            selected = ask_menu_choice(
                "选择背景净化强度",
                [("1", BACKGROUND_LABELS[BACKGROUND_STANDARD]), ("2", BACKGROUND_LABELS[BACKGROUND_STRONG])],
                default="1" if state.background_cleanup == BACKGROUND_STANDARD else "2",
            )
            state.background_cleanup = BACKGROUND_STANDARD if selected == "1" else BACKGROUND_STRONG
        elif choice == "4":
            selected = ask_menu_choice(
                "选择文字模式",
                [("1", TEXT_MODE_LABELS[TEXT_MODE_FAITHFUL]), ("2", TEXT_MODE_LABELS[TEXT_MODE_CLEAR])],
                default="1" if state.text_mode == TEXT_MODE_FAITHFUL else "2",
            )
            state.text_mode = TEXT_MODE_FAITHFUL if selected == "1" else TEXT_MODE_CLEAR
        elif choice == "5":
            selected = ask_menu_choice(
                "选择偏好焦点",
                [(str(index + 1), FOCUS_LABELS[key]) for index, key in enumerate(PREFERENCE_CHOICES)],
                default=str(PREFERENCE_CHOICES.index(state.focus) + 1),
            )
            state.focus = PREFERENCE_CHOICES[int(selected) - 1]
        elif choice == "6":
            state.note = ask_text("请输入默认备注", default=state.note or None).strip()
        elif choice == "7":
            state.auto_open_result = ask_yes_no("完成后自动打开 PPTX 吗？", default=state.auto_open_result)
        elif choice == "8":
            directory = ask_text("请输入默认输出目录，留空表示跟随输入目录", default=state.output_dir or None).strip()
            if directory:
                candidate = Path(directory).expanduser()
                if not candidate.exists():
                    candidate.mkdir(parents=True, exist_ok=True)
                state.output_dir = str(candidate.resolve())
            else:
                state.output_dir = ""
        elif choice == "9":
            state.output_suffix = sanitize_suffix(ask_text("请输入默认文件名后缀", default=state.output_suffix or "_Result"))
        elif choice == "10":
            state.diagnostic_logs = ask_yes_no("启用诊断日志吗？", default=state.diagnostic_logs)
        save_state(state)


def make_unique_output_path(candidate: Path) -> Path:
    if not candidate.exists():
        return candidate
    stem = candidate.stem
    suffix = candidate.suffix
    for index in range(2, 100):
        sibling = candidate.with_name(f"{stem}_{index}{suffix}")
        if not sibling.exists():
            return sibling
    return candidate


def suggest_output_path(state: TerminalUIState, input_path: Path) -> Path:
    base_dir = Path(state.output_dir).expanduser() if state.output_dir else (input_path if input_path.is_dir() else input_path.parent)
    if base_dir.is_file():
        base_dir = base_dir.parent
    base_dir.mkdir(parents=True, exist_ok=True)
    stem = input_path.stem if input_path.is_file() else input_path.name
    return make_unique_output_path(base_dir / f"{stem}{sanitize_suffix(state.output_suffix)}.pptx")


def build_app_settings(state: TerminalUIState) -> AppSettings:
    settings = AppSettings()
    settings.preferred_renderer = state.preferred_renderer
    settings.pdf_quality_dpi = state.pdf_quality_dpi
    settings.background_cleanup = state.background_cleanup
    settings.text_mode = state.text_mode
    settings.diagnostic_logs = state.diagnostic_logs
    return settings


def build_task_preferences(state: TerminalUIState) -> TaskPreferences:
    return TaskPreferences(focus=state.focus, note=state.note)


def run_conversion_wizard(state: TerminalUIState) -> None:
    print_header("开始转换")
    sample_default = ""
    if not state.last_input_path:
        sample = PROJECT_ROOT / "test" / "Slide1.JPG"
        if sample.exists():
            sample_default = str(sample)
    default_input = state.last_input_path or sample_default or None
    input_path = ask_existing_path("请输入 PDF / 图片 / 图片目录路径", default=default_input, expect_dir=None)

    try:
        input_kind = infer_input_kind(str(input_path))
    except Exception as exc:
        print(f"无法识别输入类型: {exc}")
        pause()
        return

    suggested_output = suggest_output_path(state, input_path)
    output_value = ask_text("输出 PPTX 路径", default=str(suggested_output))
    output_path = Path(output_value).expanduser()
    if output_path.suffix.lower() != ".pptx":
        output_path = output_path.with_suffix(".pptx")
    try:
        output_path = output_path.resolve()
    except OSError:
        pass

    focus_selected = ask_menu_choice(
        "选择本次转换偏好",
        [(str(index + 1), FOCUS_LABELS[key]) for index, key in enumerate(PREFERENCE_CHOICES)],
        default=str(PREFERENCE_CHOICES.index(state.focus) + 1),
    )
    state.focus = PREFERENCE_CHOICES[int(focus_selected) - 1]
    state.note = ask_text("补充备注（可留空）", default=state.note or None).strip()
    auto_open = ask_yes_no("完成后自动打开结果吗？", default=state.auto_open_result)
    state.auto_open_result = auto_open
    state.last_input_path = str(input_path)
    state.output_dir = str(output_path.parent)
    save_state(state)

    apply_model_env(state)
    reset_cached_runtimes()

    print()
    print("当前设置")
    print(f"  输入类型: {input_kind}")
    print(f"  输出文件: {output_path}")
    print(f"  渲染模式: {RENDERER_LABELS[state.preferred_renderer]}")
    print(f"  偏好焦点: {FOCUS_LABELS[state.focus]}")
    print()
    if not ask_yes_no("确认开始转换吗？", default=True):
        return

    print()
    print("开始执行转换...")
    print("-" * 72)

    def progress_cb(stage: str, percent: int, detail: str) -> None:
        print(f"[{percent:>3}%] {stage} | {detail}")

    def log_cb(message: str) -> None:
        print(message)

    try:
        result = run_conversion(
            str(input_path),
            output_path=str(output_path),
            input_kind=input_kind,
            auto_open=auto_open,
            progress_cb=progress_cb,
            log_cb=log_cb,
            settings=build_app_settings(state),
            preferences=build_task_preferences(state),
        )
    except Exception as exc:
        print("-" * 72)
        print(f"转换失败: {exc}")
        pause()
        return

    print("-" * 72)
    print("转换完成")
    print(f"  输出文件: {result['output_path']}")
    print(f"  渲染结果: {'高保真模式' if result.get('renderer') == 'node' else '兼容模式'}")
    print(f"  处理页数: {result['slides_processed']}")
    if result.get("fallback_notice"):
        print("  注意:")
        for line in str(result["fallback_notice"]).splitlines():
            print(f"    {line}")
    if result.get("diagnostic_log_path"):
        print(f"  诊断日志: {result['diagnostic_log_path']}")
    print()

    if not auto_open:
        if ask_yes_no("现在打开输出文件吗？", default=False):
            if not open_path_in_shell(result["output_path"]):
                print("无法直接打开输出文件。")
        if ask_yes_no("现在打开输出目录吗？", default=False):
            if not open_path_in_shell(Path(result["output_path"]).parent):
                print("无法直接打开输出目录。")
    pause()


def open_common_dirs(state: TerminalUIState) -> None:
    runtime_info, _, _ = describe_active_status(state)
    dirs = {
        "1": ("项目根目录", PROJECT_ROOT),
        "2": ("LaMa 模型目录", lama_model_slot(PROJECT_ROOT).parent),
        "3": ("OCR 模型目录", ocr_model_slot_dir(PROJECT_ROOT)),
        "4": ("日志目录", Path(runtime_info["log_dir"])),
        "0": ("返回", None),
    }
    print_header("打开常用目录")
    choice = ask_menu_choice(
        "请选择目录",
        [(key, label) for key, (label, _) in dirs.items()],
        default="0",
    )
    if choice == "0":
        return
    target = dirs[choice][1]
    assert target is not None
    target.mkdir(parents=True, exist_ok=True)
    if open_path_in_shell(target):
        print(f"已尝试打开: {target}")
    else:
        print(f"无法直接打开，请手动查看: {target}")
    pause()


def reset_terminal_state(state: TerminalUIState) -> TerminalUIState:
    print_header("重置终端配置")
    if not ask_yes_no("确定要重置终端 UI 保存的设置吗？这不会删除模型文件。", default=False):
        return state
    new_state = TerminalUIState()
    save_state(new_state)
    apply_model_env(new_state)
    reset_cached_runtimes()
    print("已重置。")
    pause()
    return new_state


def run_quick_start_wizard(state: TerminalUIState) -> None:
    print_header("快速开始向导")
    print("这个向导会带你从环境检查开始，到模型准备，再到执行一次真实转换。")
    print()
    pause("按 Enter 开始...")

    show_environment_status(state)

    _, lama_info, ocr_info = describe_active_status(state)
    if not lama_info["available"]:
        print_header("LaMa 模型")
        print(lama_info["message"])
        print()
        if ask_yes_no("你现在有本地 big-lama.pt 文件，并想复制到预留槽位吗？", default=False):
            copy_lama_model_to_slot()

    if ask_yes_no("要不要现在下载 OCR 官方模型到预留槽位？不下载也可以继续使用内置模型。", default=False):
        run_ocr_download()

    state.first_run_complete = True
    save_state(state)
    run_conversion_wizard(state)


def main_menu(state: TerminalUIState) -> TerminalUIState:
    while True:
        runtime_info, lama_info, ocr_info = describe_active_status(state)
        print_header("主菜单")
        print(f"高保真渲染: {'可用' if runtime_info['high_fidelity_available'] else '不可用'}")
        print(f"LaMa: {lama_info['message']}")
        print(f"OCR: {ocr_info['message']}")
        print()
        choice = ask_menu_choice(
            "请选择操作",
            [
                ("1", "快速开始向导"),
                ("2", "查看环境状态"),
                ("3", "模型配置"),
                ("4", "转换默认设置"),
                ("5", "开始转换"),
                ("6", "打开常用目录"),
                ("7", "重置终端配置"),
                ("0", "退出"),
            ],
            default="1" if not state.first_run_complete else "5",
        )
        if choice == "0":
            return state
        if choice == "1":
            run_quick_start_wizard(state)
        elif choice == "2":
            show_environment_status(state)
        elif choice == "3":
            configure_models_menu(state)
        elif choice == "4":
            configure_defaults_menu(state)
        elif choice == "5":
            run_conversion_wizard(state)
        elif choice == "6":
            open_common_dirs(state)
        elif choice == "7":
            state = reset_terminal_state(state)


def main() -> int:
    if not sys.stdin.isatty():
        print("terminal_ui.py 需要在交互式终端中运行。")
        return 1

    state = load_state()
    apply_model_env(state)
    reset_cached_runtimes()

    if not state.first_run_complete and ask_yes_no("检测到你可能是首次使用。现在进入快速开始向导吗？", default=True):
        run_quick_start_wizard(state)

    main_menu(state)
    clear_screen()
    print("已退出 Terminal UI。")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\n已中断。")
        raise SystemExit(130)
