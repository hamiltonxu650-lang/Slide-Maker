from __future__ import annotations

import os
from PIL import Image
import numpy as np
from services.app_models import describe_lama_model_setup
from services.runtime_env import detect_project_root


_LAMA_INSTANCE = None


def get_lama_model_status() -> dict:
    return describe_lama_model_setup(detect_project_root())


def reset_lama_runtime() -> None:
    global _LAMA_INSTANCE
    _LAMA_INSTANCE = None


def _get_lama():
    global _LAMA_INSTANCE
    if _LAMA_INSTANCE is not None:
        return _LAMA_INSTANCE

    status = get_lama_model_status()
    if not status["available"]:
        raise RuntimeError(status["message"])

    os.environ["LAMA_MODEL"] = status["model_path"]

    from simple_lama_inpainting import SimpleLama

    _LAMA_INSTANCE = SimpleLama()
    return _LAMA_INSTANCE

def inpaint_image_lama(original_image: Image.Image, mask_array: np.ndarray) -> Image.Image:
    """
    Uses LaMa (Large Mask Inpainting) AI to perfectly hallucinate and rebuild the 
    masked background textures.
    original_image: PIL Image (RGB)
    mask_array: A numpy binary mask (where 255 is the area to remove)
    """
    if original_image.mode != 'RGB':
        original_image = original_image.convert('RGB')
        
    mask_image = Image.fromarray(mask_array).convert('L')
    
    result = _get_lama()(original_image, mask_image)
    return result
