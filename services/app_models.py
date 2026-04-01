from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
import os
import re


APP_BRAND = "Slide Maker"
SETTINGS_ORG = "SlideMaker"
SETTINGS_APP = "Slide Maker"

PREFERENCE_LAYOUT = "layout"
PREFERENCE_CLARITY = "clarity"
PREFERENCE_CLEANUP = "cleanup"
PREFERENCE_SPEED = "speed"
PREFERENCE_CHOICES = (
    PREFERENCE_LAYOUT,
    PREFERENCE_CLARITY,
    PREFERENCE_CLEANUP,
    PREFERENCE_SPEED,
)

OUTPUT_POLICY_ASK = "ask"
OUTPUT_POLICY_SOURCE = "source"
OUTPUT_POLICY_LAST = "last"
OUTPUT_POLICIES = (
    OUTPUT_POLICY_ASK,
    OUTPUT_POLICY_SOURCE,
    OUTPUT_POLICY_LAST,
)

RENDERER_HIGH_FIDELITY = "high_fidelity"
RENDERER_COMPATIBILITY = "compatibility"
RENDERER_CHOICES = (
    RENDERER_HIGH_FIDELITY,
    RENDERER_COMPATIBILITY,
)

BACKGROUND_STANDARD = "standard"
BACKGROUND_STRONG = "strong"
BACKGROUND_CHOICES = (
    BACKGROUND_STANDARD,
    BACKGROUND_STRONG,
)

TEXT_MODE_FAITHFUL = "faithful"
TEXT_MODE_CLEAR = "clear"
TEXT_MODE_CHOICES = (
    TEXT_MODE_FAITHFUL,
    TEXT_MODE_CLEAR,
)

PDF_DPI_CHOICES = (150, 200, 300)
LAMA_MODEL_FILENAME = "big-lama.pt"
LAMA_MODEL_ENV_VARS = (
    "SLIDE_MAKER_LAMA_MODEL",
    "LAMA_MODEL",
)
OCR_MODEL_FILENAMES = {
    "det": "ch_PP-OCRv4_det_infer.onnx",
    "cls": "ch_ppocr_mobile_v2.0_cls_infer.onnx",
    "rec": "ch_PP-OCRv4_rec_infer.onnx",
}
OCR_MODEL_ENV_VARS = {
    "det": "SLIDE_MAKER_OCR_DET_MODEL",
    "cls": "SLIDE_MAKER_OCR_CLS_MODEL",
    "rec": "SLIDE_MAKER_OCR_REC_MODEL",
}
OCR_MODEL_DOWNLOADS = {
    "det": {
        "filename": OCR_MODEL_FILENAMES["det"],
        "url": "https://www.modelscope.cn/models/RapidAI/RapidOCR/resolve/v3.7.0/onnx/PP-OCRv4/det/ch_PP-OCRv4_det_infer.onnx",
        "sha256": "d2a7720d45a54257208b1e13e36a8479894cb74155a5efe29462512d42f49da9",
    },
    "cls": {
        "filename": OCR_MODEL_FILENAMES["cls"],
        "url": "https://www.modelscope.cn/models/RapidAI/RapidOCR/resolve/v3.7.0/onnx/PP-OCRv4/cls/ch_ppocr_mobile_v2.0_cls_infer.onnx",
        "sha256": "e47acedf663230f8863ff1ab0e64dd2d82b838fceb5957146dab185a89d6215c",
    },
    "rec": {
        "filename": OCR_MODEL_FILENAMES["rec"],
        "url": "https://www.modelscope.cn/models/RapidAI/RapidOCR/resolve/v3.7.0/onnx/PP-OCRv4/rec/ch_PP-OCRv4_rec_infer.onnx",
        "sha256": "48fc40f24f6d2a207a2b1091d3437eb3cc3eb6b676dc3ef9c37384005483683b",
    },
}


@dataclass
class AppSettings:
    remember_recent_tasks: bool = True
    output_location_policy: str = OUTPUT_POLICY_ASK
    last_output_dir: str = ""
    output_suffix: str = "_Result"
    open_pptx_after_conversion: bool = False
    open_folder_after_conversion: bool = False
    preferred_renderer: str = RENDERER_HIGH_FIDELITY
    pdf_quality_dpi: int = 200
    background_cleanup: str = BACKGROUND_STANDARD
    text_mode: str = TEXT_MODE_FAITHFUL
    diagnostic_logs: bool = True
    enable_document_scanner: bool = False

    @classmethod
    def from_dict(cls, data: dict | None) -> "AppSettings":
        data = dict(data or {})
        cleaned = cls()
        for key in cleaned.to_dict():
            if key in data:
                setattr(cleaned, key, data[key])

        if cleaned.output_location_policy not in OUTPUT_POLICIES:
            cleaned.output_location_policy = OUTPUT_POLICY_ASK
        if cleaned.preferred_renderer not in RENDERER_CHOICES:
            cleaned.preferred_renderer = RENDERER_HIGH_FIDELITY
        if cleaned.background_cleanup not in BACKGROUND_CHOICES:
            cleaned.background_cleanup = BACKGROUND_STANDARD
        if cleaned.text_mode not in TEXT_MODE_CHOICES:
            cleaned.text_mode = TEXT_MODE_FAITHFUL
        if int(cleaned.pdf_quality_dpi) not in PDF_DPI_CHOICES:
            cleaned.pdf_quality_dpi = 200
        cleaned.pdf_quality_dpi = int(cleaned.pdf_quality_dpi)
        cleaned.output_suffix = str(cleaned.output_suffix or "_Result")
        cleaned.last_output_dir = str(cleaned.last_output_dir or "")
        return cleaned

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class TaskPreferences:
    focus: str = PREFERENCE_LAYOUT
    note: str = ""
    mapped_tags: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict | None) -> "TaskPreferences":
        data = dict(data or {})
        cleaned = cls()
        for key in ("focus", "note", "mapped_tags"):
            if key in data:
                setattr(cleaned, key, data[key])
        if cleaned.focus not in PREFERENCE_CHOICES:
            cleaned.focus = PREFERENCE_LAYOUT
        cleaned.note = str(cleaned.note or "").strip()
        raw_tags = cleaned.mapped_tags
        if not isinstance(raw_tags, list):
            raw_tags = []
        cleaned.mapped_tags = [str(tag) for tag in raw_tags if str(tag).strip()]
        return cleaned

    def with_mapped_tags(self) -> "TaskPreferences":
        return TaskPreferences(
            focus=self.focus,
            note=self.note,
            mapped_tags=map_note_keywords(self.note),
        )

    def to_dict(self) -> dict:
        return asdict(self)


def map_note_keywords(note: str) -> list[str]:
    lowered = str(note or "").strip().lower()
    if not lowered:
        return []

    keyword_groups = {
        "layout": ("排版", "版式", "对齐", "还原", "错位", "位置", "layout", "align"),
        "clarity": ("清晰", "清楚", "可读", "文字", "字体", "模糊", "readable", "clear"),
        "cleanup": ("背景", "去字", "干净", "残影", "水印", "遮罩", "background", "clean"),
        "speed": ("速度", "更快", "快速", "省时", "fast", "speed"),
        "scan": ("扫描", "裁正", "边框", "歪", "梯形", "透视", "矫正", "scan"),
    }
    tags = []
    for tag, keywords in keyword_groups.items():
        if any(word in lowered for word in keywords):
            tags.append(tag)
    return tags


def build_conversion_options(settings: AppSettings | None, preferences: TaskPreferences | None) -> dict:
    settings = settings or AppSettings()
    preferences = (preferences or TaskPreferences()).with_mapped_tags()

    preferred_renderer = settings.preferred_renderer
    pdf_dpi = settings.pdf_quality_dpi
    background_cleanup = settings.background_cleanup
    text_mode = settings.text_mode

    if preferences.focus == PREFERENCE_LAYOUT:
        preferred_renderer = RENDERER_HIGH_FIDELITY
        text_mode = TEXT_MODE_FAITHFUL
    elif preferences.focus == PREFERENCE_CLARITY:
        text_mode = TEXT_MODE_CLEAR
    elif preferences.focus == PREFERENCE_CLEANUP:
        background_cleanup = BACKGROUND_STRONG
    elif preferences.focus == PREFERENCE_SPEED:
        preferred_renderer = RENDERER_COMPATIBILITY
        pdf_dpi = 150

    if "clarity" in preferences.mapped_tags:
        text_mode = TEXT_MODE_CLEAR
    if "cleanup" in preferences.mapped_tags:
        background_cleanup = BACKGROUND_STRONG
    if "speed" in preferences.mapped_tags:
        pdf_dpi = min(pdf_dpi, 150)
    if "layout" in preferences.mapped_tags and preferences.focus != PREFERENCE_SPEED:
        preferred_renderer = RENDERER_HIGH_FIDELITY

    if text_mode == TEXT_MODE_CLEAR:
        font_scale = 1.08
        box_scale = 1.85
    else:
        font_scale = 0.96
        box_scale = 1.50

    if background_cleanup == BACKGROUND_STRONG:
        cleanup_options = {
            "mask_padding": 16,
            "color_tolerance": 185,
            "dilate_kernel": 11,
            "dilate_iterations": 3,
        }
    else:
        cleanup_options = {
            "mask_padding": 12,
            "color_tolerance": 150,
            "dilate_kernel": 9,
            "dilate_iterations": 2,
        }

    return {
        "preferred_renderer": preferred_renderer,
        "pdf_dpi": int(pdf_dpi),
        "ocr_max_long_edge": 3200,
        "background_cleanup": background_cleanup,
        "text_mode": text_mode,
        "font_scale": font_scale,
        "box_scale": box_scale,
        "cleanup_options": cleanup_options,
        "preference_focus": preferences.focus,
        "preference_tags": list(preferences.mapped_tags),
        "user_note": preferences.note,
        "enable_document_scanner": bool(settings.enable_document_scanner or ("scan" in preferences.mapped_tags)),
    }


def app_data_root(project_root: Path | None = None) -> Path:
    local_appdata = os.getenv("LOCALAPPDATA")
    if local_appdata:
        return Path(local_appdata) / "SlideMaker"
    if project_root is not None:
        return Path(project_root) / ".slide_maker_data"
    return Path.cwd() / ".slide_maker_data"


def lama_model_slot(project_root: Path | None = None) -> Path:
    slot = app_data_root(project_root) / "models" / "lama" / LAMA_MODEL_FILENAME
    slot.parent.mkdir(parents=True, exist_ok=True)
    return slot


def ocr_model_slot_dir(project_root: Path | None = None) -> Path:
    slot_dir = app_data_root(project_root) / "models" / "rapidocr" / "onnxruntime"
    slot_dir.mkdir(parents=True, exist_ok=True)
    return slot_dir


def ocr_model_slot(model_kind: str, project_root: Path | None = None) -> Path:
    if model_kind not in OCR_MODEL_FILENAMES:
        raise KeyError(f"Unknown OCR model kind: {model_kind}")
    return ocr_model_slot_dir(project_root) / OCR_MODEL_FILENAMES[model_kind]


def describe_ocr_model_setup(project_root: Path | None = None) -> dict:
    slot_dir = ocr_model_slot_dir(project_root)
    models = {}
    invalid_entries = []
    custom_model_count = 0

    for model_kind, filename in OCR_MODEL_FILENAMES.items():
        env_var = OCR_MODEL_ENV_VARS[model_kind]
        slot_path = ocr_model_slot(model_kind, project_root)
        info = {
            "kind": model_kind,
            "filename": filename,
            "env_var": env_var,
            "slot_path": str(slot_path),
            "path": "",
            "source": "packaged",
            "configured": False,
            "valid": False,
            "download_url": OCR_MODEL_DOWNLOADS[model_kind]["url"],
            "sha256": OCR_MODEL_DOWNLOADS[model_kind]["sha256"],
        }

        raw_path = str(os.getenv(env_var, "") or "").strip()
        if raw_path:
            info["configured"] = True
            candidate = Path(raw_path).expanduser()
            try:
                candidate = candidate.resolve()
            except OSError:
                pass
            info["path"] = str(candidate)
            info["source"] = env_var
            if candidate.exists() and candidate.is_file():
                info["valid"] = True
                custom_model_count += 1
            else:
                invalid_entries.append(f"{env_var}: {candidate}")
        elif slot_path.exists() and slot_path.is_file():
            info["configured"] = True
            info["path"] = str(slot_path)
            info["source"] = "slot"
            info["valid"] = True
            custom_model_count += 1

        models[model_kind] = info

    if invalid_entries:
        message = (
            "检测到无效的 OCR 自定义模型路径，将回退到 RapidOCR 内置模型："
            + "；".join(invalid_entries)
        )
    elif custom_model_count == len(OCR_MODEL_FILENAMES):
        message = "OCR 模型已就绪，当前 3 个模型都来自自定义槽位或环境变量。"
    elif custom_model_count > 0:
        message = (
            f"OCR 自定义模型已接入 {custom_model_count}/3，"
            "未提供的部分仍使用 RapidOCR 内置模型。"
        )
    else:
        message = (
            f"当前使用 RapidOCR 内置模型。你可以把 3 个 ONNX 文件放到 {slot_dir}，"
            "或设置 SLIDE_MAKER_OCR_DET_MODEL / SLIDE_MAKER_OCR_CLS_MODEL / "
            "SLIDE_MAKER_OCR_REC_MODEL。"
        )

    return {
        "slot_dir": str(slot_dir),
        "models": models,
        "custom_model_count": custom_model_count,
        "custom_model_complete": custom_model_count == len(OCR_MODEL_FILENAMES),
        "has_invalid_custom_model": bool(invalid_entries),
        "invalid_entries": list(invalid_entries),
        "message": message,
    }


def describe_lama_model_setup(project_root: Path | None = None) -> dict:
    slot = lama_model_slot(project_root)

    for env_var in LAMA_MODEL_ENV_VARS:
        raw_path = str(os.getenv(env_var, "") or "").strip()
        if not raw_path:
            continue

        candidate = Path(raw_path).expanduser()
        try:
            candidate = candidate.resolve()
        except OSError:
            pass

        if candidate.exists() and candidate.is_file():
            return {
                "available": True,
                "model_path": str(candidate),
                "slot_path": str(slot),
                "source": env_var,
                "message": f"LaMa 模型已就绪，当前使用 {env_var} 指向的文件。",
            }

        return {
            "available": False,
            "model_path": str(candidate),
            "slot_path": str(slot),
            "source": env_var,
            "message": f"环境变量 {env_var} 指向的模型不存在：{candidate}",
        }

    if slot.exists() and slot.is_file():
        return {
            "available": True,
            "model_path": str(slot),
            "slot_path": str(slot),
            "source": "slot",
            "message": "LaMa 模型已就绪，当前使用预留模型槽位中的文件。",
        }

    return {
        "available": False,
        "model_path": "",
        "slot_path": str(slot),
        "source": "slot",
        "message": (
            f"未检测到 LaMa 模型。请将 {LAMA_MODEL_FILENAME} 放到 {slot}，"
            "或设置环境变量 SLIDE_MAKER_LAMA_MODEL 指向你自己下载的模型文件。"
        ),
    }


def build_log_path(project_root: Path | None = None) -> Path:
    log_dir = app_data_root(project_root) / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    from datetime import datetime

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return log_dir / f"slide-maker-{stamp}.log"


def sanitize_suffix(value: str) -> str:
    cleaned = str(value or "").strip()
    cleaned = re.sub(r'[<>:"/\\\\|?*]+', "_", cleaned)
    return cleaned or "_Result"
