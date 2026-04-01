from __future__ import annotations

from pathlib import Path
import shutil
import tempfile

from fastapi import BackgroundTasks, FastAPI, File, Form, Request, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from services.app_models import (
    AppSettings,
    PREFERENCE_CHOICES,
    PREFERENCE_CLARITY,
    PREFERENCE_CLEANUP,
    PREFERENCE_LAYOUT,
    PREFERENCE_SPEED,
    TaskPreferences,
)
from services.conversion_service import run_conversion
from services.runtime_env import describe_runtime_environment


BASE_DIR = Path(__file__).resolve().parent
WEB_DIR = BASE_DIR / "web"
SUPPORTED_UPLOAD_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg"}
FOCUS_LABELS = {
    PREFERENCE_LAYOUT: "排版优先",
    PREFERENCE_CLARITY: "文字清晰",
    PREFERENCE_CLEANUP: "背景干净",
    PREFERENCE_SPEED: "速度优先",
}

app = FastAPI(title="Slide Maker Web", version="1.0.0")
app.mount("/static", StaticFiles(directory=str(WEB_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(WEB_DIR / "templates"))


def _render_home(request: Request, error: str = "", selected_focus: str = PREFERENCE_LAYOUT, note: str = "", enable_scan: bool = False):
    runtime = describe_runtime_environment()
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "error": error,
            "note": note,
            "enable_scan": enable_scan,
            "selected_focus": selected_focus,
            "focus_options": [
                {"value": value, "label": FOCUS_LABELS.get(value, value)}
                for value in PREFERENCE_CHOICES
            ],
            "runtime": runtime,
        },
    )


def _safe_upload_name(filename: str | None) -> tuple[str, str]:
    candidate = Path(filename or "upload")
    suffix = candidate.suffix.lower()
    if suffix not in SUPPORTED_UPLOAD_EXTENSIONS:
        raise ValueError("仅支持上传 PDF、PNG、JPG、JPEG 文件。")
    stem = candidate.stem.strip() or "upload"
    safe_stem = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in stem).strip("_")
    return (safe_stem or "upload"), suffix


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return _render_home(request)


@app.get("/healthz")
async def healthz():
    runtime = describe_runtime_environment()
    return {
        "status": "ok",
        "high_fidelity_available": runtime["high_fidelity_available"],
        "node_path": runtime["node_path"],
    }


@app.post("/api/detect-corners")
async def api_detect_corners(file: UploadFile = File(...)):
    import cv2, numpy as np
    from scanner_engine import detect_document_corners
    content = await file.read()
    img = cv2.imdecode(np.frombuffer(content, np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        return {"status": "error", "message": "Invalid image"}
    pts = detect_document_corners(img)
    return {"status": "ok", "points": pts.tolist()}


@app.post("/convert")
async def convert(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    focus: str = Form(PREFERENCE_LAYOUT),
    note: str = Form(""),
    enable_scan: bool = Form(False),
    crop_points: str = Form(""),
):
    if focus not in PREFERENCE_CHOICES:
        return _render_home(request, error="转换重点无效，请重新选择。", selected_focus=PREFERENCE_LAYOUT, note=note, enable_scan=enable_scan)

    try:
        safe_stem, suffix = _safe_upload_name(file.filename)
    except ValueError as exc:
        return _render_home(request, error=str(exc), selected_focus=focus, note=note, enable_scan=enable_scan)

    temp_root = Path(tempfile.mkdtemp(prefix="slide-maker-web-"))
    input_path = temp_root / f"input{suffix}"
    output_path = temp_root / f"{safe_stem}_Result.pptx"

    try:
        with input_path.open("wb") as handle:
            shutil.copyfileobj(file.file, handle)

        if crop_points:
            import json, cv2, numpy as np
            from scanner_engine import four_point_transform, enhance_scanned_document
            try:
                pts = np.array(json.loads(crop_points), dtype=np.float32)
                img = cv2.imread(str(input_path))
                if img is not None:
                    warped = four_point_transform(img, pts)
                    enhanced = enhance_scanned_document(warped, mode="color_enhance")
                    cv2.imwrite(str(input_path), enhanced)
                    enable_scan = False
            except Exception as e:
                print(f"Error parsing crop points: {e}")

        settings = AppSettings(
            open_pptx_after_conversion=False,
            open_folder_after_conversion=False,
            diagnostic_logs=True,
            enable_document_scanner=enable_scan,
        )
        preferences = TaskPreferences(focus=focus, note=note)
        await run_in_threadpool(
            run_conversion,
            str(input_path),
            str(output_path),
            None,
            False,
            None,
            None,
            settings,
            preferences,
        )
    except Exception as exc:
        shutil.rmtree(temp_root, ignore_errors=True)
        return _render_home(request, error=f"转换失败：{exc}", selected_focus=focus, note=note, enable_scan=enable_scan)
    finally:
        await file.close()

    background_tasks.add_task(shutil.rmtree, temp_root, ignore_errors=True)
    return FileResponse(
        path=str(output_path),
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        filename=output_path.name,
    )
