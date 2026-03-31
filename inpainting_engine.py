import os
from typing import Optional


def _is_lfs_pointer_file(path: str) -> bool:
    try:
        if not os.path.exists(path) or os.path.getsize(path) > 1024:
            return False
        with open(path, "r", encoding="utf-8", errors="ignore") as handle:
            header = handle.read(128)
        return header.startswith("version https://git-lfs.github.com/spec/v1")
    except OSError:
        return False


# Standardize model path for portability
local_model = os.path.join(os.path.dirname(__file__), "models", "big-lama.pt")
if os.path.exists(local_model) and not _is_lfs_pointer_file(local_model):
    os.environ["LAMA_MODEL"] = local_model
else:
    os.environ.pop("LAMA_MODEL", None)

from PIL import Image
import numpy as np
import torch
from simple_lama_inpainting.models.model import LAMA_MODEL_URL
from simple_lama_inpainting.utils import download_model, prepare_img_and_mask

_LAMA = None


class _SafeSimpleLama:
    def __init__(self, device: Optional[torch.device] = None) -> None:
        self.device = device or torch.device("cpu")
        model_path = os.environ.get("LAMA_MODEL")
        if model_path:
            if not os.path.exists(model_path):
                raise FileNotFoundError(f"lama torchscript model not found: {model_path}")
        else:
            model_path = download_model(LAMA_MODEL_URL)

        self.model = torch.jit.load(model_path, map_location=self.device)
        self.model.eval()
        self.model.to(self.device)

    def __call__(self, image: Image.Image, mask: Image.Image) -> Image.Image:
        image, mask = prepare_img_and_mask(image, mask, self.device)
        with torch.inference_mode():
            inpainted = self.model(image, mask)
            cur_res = inpainted[0].permute(1, 2, 0).detach().cpu().numpy()
            cur_res = np.clip(cur_res * 255, 0, 255).astype(np.uint8)
            return Image.fromarray(cur_res)


def _get_lama() -> _SafeSimpleLama:
    global _LAMA
    if _LAMA is None:
        _LAMA = _SafeSimpleLama()
    return _LAMA

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
