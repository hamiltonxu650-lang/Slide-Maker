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
    }


def app_data_root(project_root: Path | None = None) -> Path:
    local_appdata = os.getenv("LOCALAPPDATA")
    if local_appdata:
        return Path(local_appdata) / "SlideMaker"
    if project_root is not None:
        return Path(project_root) / ".slide_maker_data"
    return Path.cwd() / ".slide_maker_data"


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
