import re
from typing import Any

import numpy as np
from services.app_models import describe_ocr_model_setup
from services.runtime_env import detect_project_root

try:
    import wordninja
except Exception:  # pragma: no cover - packaged fallback
    wordninja = None


_OCR_ENGINE = None
_OCR_IMPORT_ERROR = None
_OCR_BACKEND = None
_OCR_MODEL_INFO = None


def reset_ocr_runtime() -> None:
    global _OCR_ENGINE, _OCR_IMPORT_ERROR, _OCR_BACKEND, _OCR_MODEL_INFO
    _OCR_ENGINE = None
    _OCR_IMPORT_ERROR = None
    _OCR_BACKEND = None
    _OCR_MODEL_INFO = None


def _build_rapidocr_kwargs() -> dict[str, str]:
    global _OCR_MODEL_INFO

    _OCR_MODEL_INFO = describe_ocr_model_setup(detect_project_root())
    kwargs = {}
    for model_kind, info in _OCR_MODEL_INFO["models"].items():
        if info["valid"] and info["path"]:
            kwargs[f"{model_kind}_model_path"] = info["path"]
    return kwargs


def _load_ocr_engine():
    global _OCR_ENGINE, _OCR_IMPORT_ERROR, _OCR_BACKEND, _OCR_MODEL_INFO
    if _OCR_BACKEND is not None:
        return _OCR_ENGINE

    try:
        from rapidocr_onnxruntime import RapidOCR

        _OCR_ENGINE = RapidOCR(**_build_rapidocr_kwargs())
        _OCR_BACKEND = "rapidocr"
        _OCR_IMPORT_ERROR = None
    except Exception as rapidocr_exc:  # pragma: no cover - depends on local runtime
        try:
            import winrt_ocr_engine

            _OCR_ENGINE = winrt_ocr_engine
            _OCR_BACKEND = "winrt"
            _OCR_IMPORT_ERROR = rapidocr_exc
        except Exception as winrt_exc:  # pragma: no cover - depends on local runtime
            _OCR_ENGINE = None
            _OCR_BACKEND = "none"
            _OCR_MODEL_INFO = None
            _OCR_IMPORT_ERROR = RuntimeError(
                f"RapidOCR unavailable: {rapidocr_exc}; Windows OCR unavailable: {winrt_exc}"
            )
    return _OCR_ENGINE


def get_ocr_runtime_status() -> dict[str, Any]:
    engine = _load_ocr_engine()
    model_info = _OCR_MODEL_INFO or describe_ocr_model_setup(detect_project_root())
    return {
        "available": engine is not None,
        "backend": _OCR_BACKEND,
        "error": "" if _OCR_IMPORT_ERROR is None else str(_OCR_IMPORT_ERROR),
        "model_message": str(model_info["message"]),
        "custom_model_count": int(model_info["custom_model_count"]),
        "custom_model_complete": bool(model_info["custom_model_complete"]),
        "model_slot_dir": str(model_info["slot_dir"]),
        "has_invalid_custom_model": bool(model_info["has_invalid_custom_model"]),
    }

def fix_english_spacing(text):
    def repl(m):
        chunk = m.group(0)
        if len(chunk) <= 3: return chunk
        splits = wordninja.split(chunk.lower()) if wordninja else [chunk]
        if len(splits) <= 1: return chunk
        
        res = []
        idx = 0
        for s in splits:
            orig_part = chunk[idx:idx+len(s)]
            res.append(orig_part)
            idx += len(s)
        return " ".join(res)
        
    return re.sub(r'[A-Za-z]+', repl, text)

def extract_text_data(image_path, log_cb=None):
    """
    Extracts text, bounding boxes, and confidence scores from an image.
    Uses RapidOCR to ensure an ultra-lightweight App distribution size without PyTorch/Paddle.
    """
    import cv2
    import numpy as np
    # Handle Chinese filenames on Windows
    img = cv2.imdecode(np.fromfile(image_path, dtype=np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        return []

    engine = _load_ocr_engine()
    if engine is None:
        if log_cb and _OCR_IMPORT_ERROR is not None:
            log_cb(
                f"[!] OCR runtime unavailable, falling back to image-only slide output: {_OCR_IMPORT_ERROR}"
            )
        return []

    if _OCR_BACKEND == "winrt":
        if log_cb:
            log_cb("[*] RapidOCR unavailable, using Windows OCR fallback.")
        result = engine.extract_text_data(image_path)
        return _normalize_extracted_data(result)

    result, _ = engine(img)
    
    return _normalize_extracted_data(result)


def _normalize_extracted_data(result):
    extracted_data = []
    if not result:
        return extracted_data

    for res in result:
        if isinstance(res, dict):
            box = res["box"]
            raw_text = res["text"]
            score = res.get("confidence", 1.0)
        else:
            box, raw_text, score = res
        text = fix_english_spacing(raw_text)
        
        def is_shape_or_bullet(t):
            t = t.strip()
            if not t: return True
            shape_chars = set("Oo0口□○〇。・.-_vV√xX×")
            if len(t) <= 2 and all(c in shape_chars for c in t):
                return True
            return False
            
        if is_shape_or_bullet(text):
            continue
        
        # Parse points
        x_min = min(p[0] for p in box)
        y_min = min(p[1] for p in box)
        x_max = max(p[0] for p in box)
        y_max = max(p[1] for p in box)
        
        extracted_data.append({
            'box': box,
            'text': text,
            'confidence': float(score),
            'height': float(y_max - y_min),
            'width': float(x_max - x_min)
        })
        
    return extracted_data

if __name__ == "__main__":
    import sys
    test_image = sys.argv[1] if len(sys.argv) > 1 else 'test/test_image.jpg'
    print(extract_text_data(test_image))
