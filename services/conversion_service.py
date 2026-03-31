from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import sys

from services.app_models import (
    APP_BRAND,
    RENDERER_COMPATIBILITY,
    RENDERER_HIGH_FIDELITY,
    AppSettings,
    TaskPreferences,
    app_data_root,
    build_conversion_options,
    build_log_path,
    describe_lama_model_setup,
)
from services.runtime_env import describe_runtime_environment, detect_project_root, find_node_executable


SUPPORTED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg"}
STAGE_ORDER = ["校验输入", "提取页面", "OCR/去字", "生成 PPTX", "完成"]


class ConversionError(RuntimeError):
    pass


class DiagnosticLogger:
    def __init__(self, enabled: bool, project_root: Path, log_cb=None):
        self.log_cb = log_cb
        self.stdout_fallback = log_cb is None
        self.path = build_log_path(project_root) if enabled else None

    def emit(self, message: str) -> None:
        message = str(message)
        if self.path:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(message.rstrip() + "\n")

        if self.log_cb:
            self.log_cb(message)
        elif self.stdout_fallback:
            print(message)
def _emit_progress(progress_cb, stage, percent, detail):
    if progress_cb:
        progress_cb(stage, int(percent), detail)


def infer_input_kind(input_path):
    if Path(input_path).is_dir():
        return "image"
    suffix = Path(input_path).suffix.lower()
    if suffix == ".pdf":
        return "pdf"
    if suffix in SUPPORTED_IMAGE_EXTENSIONS:
        return "image"
    raise ConversionError(f"暂不支持的输入类型：{suffix or 'unknown'}")
def _resolve_output_path(input_path: str, output_path: str) -> str:
    if output_path:
        return str(Path(output_path).expanduser().resolve())
    return str(Path(input_path).with_name(f"{Path(input_path).stem}_Result.pptx"))


def _run_layout_engine(node_executable, js_engine, ocr_data_path, output_path, cwd, logger):
    command = [node_executable, js_engine, ocr_data_path, output_path]
    completed = subprocess.run(
        command,
        cwd=str(cwd),
        check=True,
        text=True,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
    )
    for stream in (completed.stdout, completed.stderr):
        if not stream:
            continue
        for line in stream.splitlines():
            line = line.strip()
            if line:
                logger.emit(line)


def run_conversion(
    input_path,
    output_path="Result_Presentation.pptx",
    input_kind=None,
    auto_open=True,
    progress_cb=None,
    log_cb=None,
    settings: AppSettings | None = None,
    preferences: TaskPreferences | None = None,
):
    project_root = detect_project_root()
    input_path = str(Path(input_path).expanduser().resolve())
    output_path = _resolve_output_path(input_path, output_path)
    settings = AppSettings.from_dict(settings.to_dict() if isinstance(settings, AppSettings) else settings)
    preferences = TaskPreferences.from_dict(preferences.to_dict() if isinstance(preferences, TaskPreferences) else preferences)
    options = build_conversion_options(settings, preferences)
    logger = DiagnosticLogger(settings.diagnostic_logs, project_root, log_cb=log_cb)
    lama_info = describe_lama_model_setup(project_root)
    fallback_messages = []

    if not os.path.exists(input_path):
        raise FileNotFoundError(f"输入文件不存在：{input_path}")

    if input_kind is None:
        input_kind = infer_input_kind(input_path)
    options["canvas_dpi"] = int(options["pdf_dpi"]) if input_kind == "pdf" else 96

    if input_kind not in {"pdf", "image"}:
        raise ConversionError("当前版本只支持 PDF 和图片转 PPTX。")

    if input_kind == "image" and Path(input_path).suffix.lower() not in SUPPORTED_IMAGE_EXTENSIONS:
        raise ConversionError("图片输入目前仅支持 PNG、JPG、JPEG。")

    _emit_progress(progress_cb, "校验输入", 5, "正在检查输入路径与输出位置")
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    session_root = app_data_root(project_root) / "runtime" / Path(output_path).stem
    session_root.mkdir(parents=True, exist_ok=True)
    temp_extract_dir = session_root / "extracted"
    working_dir = session_root / "working"
    working_dir.mkdir(parents=True, exist_ok=True)

    logger.emit(f"[*] Brand: {APP_BRAND}")
    logger.emit(f"[*] Input kind: {input_kind}")
    logger.emit(f"[*] Output path: {output_path}")
    logger.emit(f"[*] Preference focus: {options['preference_focus']}")
    if not lama_info["available"]:
        logger.emit(f"[!] {lama_info['message']}")
        fallback_messages.append(
            f"未检测到 LaMa 模型，背景修复将回退到 OpenCV。"
            f"请将 big-lama.pt 放到 {lama_info['slot_path']}，"
            "或设置环境变量 SLIDE_MAKER_LAMA_MODEL。"
        )
    if options["preference_tags"]:
        logger.emit(f"[*] Mapped note tags: {', '.join(options['preference_tags'])}")
    if options["user_note"]:
        logger.emit(f"[*] User note: {options['user_note']}")

    source_processed_path = input_path
    if input_kind == "pdf":
        from extract_pdf import extract_pdf_to_images

        _emit_progress(progress_cb, "提取页面", 15, "PDF 正在拆分为图片")
        if temp_extract_dir.exists():
            shutil.rmtree(temp_extract_dir)

        def on_pdf_progress(done, total, out_file):
            ratio = done / max(total, 1)
            percent = 15 + int(ratio * 15)
            _emit_progress(progress_cb, "提取页面", percent, f"已提取第 {done}/{total} 页")

        extract_pdf_to_images(
            input_path,
            str(temp_extract_dir),
            dpi=options["pdf_dpi"],
            progress_cb=on_pdf_progress,
            log_cb=logger.emit,
        )
        source_processed_path = str(temp_extract_dir)
    else:
        _emit_progress(progress_cb, "提取页面", 30, "图片输入无需拆页，直接进入识别")

    _emit_progress(progress_cb, "OCR/去字", 35, "开始执行 OCR 与背景修复")

    def on_slide_progress(done, total, message):
        ratio = done / max(total, 1)
        percent = 35 + int(ratio * 40)
        _emit_progress(progress_cb, "OCR/去字", percent, message)

    from main import process_images_to_ppt

    process_result = process_images_to_ppt(
        source_processed_path,
        output_ppt=output_path,
        slide_progress_cb=on_slide_progress,
        log_cb=logger.emit,
        options=options,
        working_dir=str(working_dir),
    )

    requested_renderer = options["preferred_renderer"]
    fallback_notice = ""
    renderer = "python"
    _emit_progress(progress_cb, "生成 PPTX", 80, "正在生成可编辑 PPTX")

    if not process_result.get("ocr_runtime_available", True):
        fallback_messages.append("OCR 运行时不可用，已自动切换为兼容输出（保留原图页面）。")
        logger.emit("[!] OCR runtime unavailable. Keeping compatibility output.")
    elif requested_renderer == RENDERER_COMPATIBILITY:
        logger.emit("[*] Compatibility mode selected, keeping Python-generated PPTX.")
    else:
        node_executable = find_node_executable(project_root)
        if not node_executable:
            fallback_messages.append("高保真运行时不可用，已自动切换兼容模式。")
            logger.emit("[!] node.exe not found. Falling back to compatibility mode.")
        else:
            logger.emit(f"[*] Using Node runtime: {node_executable}")
            js_engine = str(project_root / "pptx-project" / "layout_engine.js")
            ocr_data = str(working_dir / "ocr_data.json")
            _emit_progress(progress_cb, "生成 PPTX", 92, "正在执行高保真排版")
            _run_layout_engine(
                node_executable,
                js_engine,
                ocr_data,
                output_path,
                project_root / "pptx-project",
                logger,
            )
            renderer = "node"

    fallback_notice = "\n".join(message for message in fallback_messages if message)

    _emit_progress(progress_cb, "完成", 100, "转换完成，可以打开结果文件")

    if auto_open and os.path.exists(output_path):
        from open_ppt_helper import ask_to_open

        ask_to_open(output_path)

    return {
        "input_path": input_path,
        "output_path": output_path,
        "input_kind": input_kind,
        "renderer": renderer,
        "requested_renderer": requested_renderer,
        "fallback_notice": fallback_notice,
        "slides_processed": process_result["slides_processed"],
        "ocr_data_path": process_result["ocr_data_path"],
        "ocr_runtime_available": process_result.get("ocr_runtime_available", True),
        "ocr_runtime_error": process_result.get("ocr_runtime_error", ""),
        "temp_extract_dir": str(temp_extract_dir) if input_kind == "pdf" else None,
        "working_dir": str(working_dir),
        "diagnostic_log_path": str(logger.path) if logger.path else "",
        "stages": STAGE_ORDER,
        "python_executable": sys.executable,
        "applied_options": options,
    }
