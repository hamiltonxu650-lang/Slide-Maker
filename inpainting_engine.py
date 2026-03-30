import os
# Standardize model path for portability
local_model = os.path.join(os.path.dirname(__file__), "models", "big-lama.pt")
if os.path.exists(local_model):
    os.environ["LAMA_MODEL"] = local_model

from simple_lama_inpainting import SimpleLama
from PIL import Image
import numpy as np

# Initialize globally to avoid reloading the big model for every slide
lama = SimpleLama()

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
    
    result = lama(original_image, mask_image)
    return result
