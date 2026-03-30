import cv2
import numpy as np
import os

LAMA_MAX_PIXELS = 12_000_000
LAMA_MAX_DIMENSION = 4096


def _emit_log(log_cb, message):
    if log_cb:
        log_cb(message)
    else:
        print(message)

def create_smart_text_mask(img, text_data, cleanup_options=None):
    """
    Creates a "Fat Worm" mask with THREE detection layers:
    1. Color Distance (catches text body pixels)
    2. Otsu Threshold (catches brightness edges)
    3. Adaptive Threshold (catches anti-aliased halos and shadows that Otsu misses)
    Then heavily dilates to ensure zero residual shadow text.
    """
    cleanup_options = dict(cleanup_options or {})
    pad = int(cleanup_options.get("mask_padding", 12))
    color_tolerance = int(cleanup_options.get("color_tolerance", 150))
    dilate_kernel = int(cleanup_options.get("dilate_kernel", 9))
    dilate_iterations = int(cleanup_options.get("dilate_iterations", 2))

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    h, w = img.shape[:2]
    mask = np.zeros((h, w), dtype=np.uint8)
    
    for td in text_data:
        box = td['box']
        pts = np.array(box, dtype=np.int32)
        x, y, bw, bh = cv2.boundingRect(pts)
        
        y1, y2 = max(0, y - pad), min(h, y + bh + pad)
        x1, x2 = max(0, x - pad), min(w, x + bw + pad)
        
        roi_gray = gray[y1:y2, x1:x2]
        roi_bgr = img[y1:y2, x1:x2]
        if roi_gray.size == 0: continue
            
        # Layer 1: Color distance mask (generous tolerance for anti-aliased gradients)
        tr, tg, tb = td.get('color', [0, 0, 0])
        target_color = np.array([tb, tg, tr], dtype=np.float32)
        color_diff = np.sum(np.abs(roi_bgr.astype(np.float32) - target_color), axis=2)
        color_mask = (color_diff < color_tolerance).astype(np.uint8) * 255
        
        # Layer 2: Otsu mask (catches strong brightness edges)
        # To determine if text is brighter than the background, explicitly find the 
        # median brightness of the non-text pixels inside the bounding box!
        non_text_pixels = roi_gray[color_mask == 0]
        bg_brightness = np.median(non_text_pixels) if len(non_text_pixels) > 0 else 127
        text_brightness = 0.299*tr + 0.587*tg + 0.114*tb
        
        text_is_brighter = text_brightness > bg_brightness
        blur = cv2.GaussianBlur(roi_gray, (3, 3), 0)
        
        if text_is_brighter:
            _, otsu_mask = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        else:
            _, otsu_mask = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        
        # Layer 3: Adaptive threshold (catches shadows and halos that global Otsu misses)
        adaptive_mask = cv2.adaptiveThreshold(
            blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV if not text_is_brighter else cv2.THRESH_BINARY,
            blockSize=max(11, (min(bw, bh) // 4) | 1),  # Must be odd
            C=5
        )
            
        # Combine all three layers
        combined_mask = np.maximum(color_mask, np.maximum(otsu_mask, adaptive_mask))
        
        # Heavy dilation: 9x9 elliptical kernel, 2 iterations
        # This extends ~8px outward from every detected text pixel, swallowing all halos
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (dilate_kernel, dilate_kernel))
        fat_text_mask = cv2.dilate(combined_mask, kernel, iterations=dilate_iterations)
        
        mask[y1:y2, x1:x2] = np.maximum(mask[y1:y2, x1:x2], fat_text_mask)
        
    return mask

def guess_local_bg(img, x, y, bw, bh):
    """
    Analyzes the 10px perimeter around a text box to determine the median background color
    and its variance (is it a flat color or a complex texture?).
    """
    h, w = img.shape[:2]
    pad = 10
    by1, by2 = max(0, y - pad), min(h, y + bh + pad)
    bx1, bx2 = max(0, x - pad), min(w, x + bw + pad)
    
    roi = img[by1:by2, bx1:bx2]
    mask = np.ones(roi.shape[:2], dtype=bool)
    
    # Exclude the text box itself
    inner_y1, inner_y2 = y - by1, y + bh - by1
    inner_x1, inner_x2 = x - bx1, x + bw - bx1
    if 0 <= inner_y1 < inner_y2 <= roi.shape[0] and 0 <= inner_x1 < inner_x2 <= roi.shape[1]:
        mask[inner_y1:inner_y2, inner_x1:inner_x2] = False
        
    border_pixels = roi[mask]
    if len(border_pixels) == 0:
        return np.array([0,0,0]), 999.0
        
    median_color = np.median(border_pixels, axis=0) # BGR
    diff = np.abs(border_pixels.astype(np.float32) - median_color)
    variance = np.mean(np.sum(diff, axis=1))
    
    return median_color, variance

def inpaint_background(image_path, text_data, output_path, use_ai=True, cleanup_options=None, log_cb=None):
    img = cv2.imdecode(np.fromfile(image_path, dtype=np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        raise FileNotFoundError(f"Cannot read image: {image_path}")
        
    result = img.copy()

    # Generate the highly precise text stroke mask for the entire image
    full_mask = create_smart_text_mask(result, text_data, cleanup_options=cleanup_options)
    
    # Run LaMa on the entire mask to guarantee perfect erasure everywhere
    if np.any(full_mask > 0):
        oversized_for_lama = (
            result.shape[0] * result.shape[1] > LAMA_MAX_PIXELS
            or max(result.shape[0], result.shape[1]) > LAMA_MAX_DIMENSION
        )
        if use_ai:
            if oversized_for_lama:
                _emit_log(
                    log_cb,
                    "[*] Skipping LaMa AI for oversized page; using OpenCV Telea directly.",
                )
                result = cv2.inpaint(result, full_mask, 7, cv2.INPAINT_TELEA)
                _emit_log(log_cb, "[*] Background repair backend: OpenCV Telea")
            else:
                try:
                    from inpainting_engine import inpaint_image_lama
                    from PIL import Image
                    pil_img = Image.fromarray(cv2.cvtColor(result, cv2.COLOR_BGR2RGB))
                    clean_pil = inpaint_image_lama(pil_img, full_mask)
                    result = cv2.cvtColor(np.array(clean_pil), cv2.COLOR_RGB2BGR)
                    _emit_log(log_cb, "[*] Background repair backend: LaMa AI")
                except Exception as e:
                    _emit_log(log_cb, f"[!] Failed to use LaMa AI, falling back to OpenCV inpaint: {e}")
                    result = cv2.inpaint(result, full_mask, 7, cv2.INPAINT_TELEA)
                    _emit_log(log_cb, "[*] Background repair backend: OpenCV Telea")
        else:
            result = cv2.inpaint(result, full_mask, 7, cv2.INPAINT_TELEA)
            _emit_log(log_cb, "[*] Background repair backend: OpenCV Telea")

    cv2.imencode('.png', result)[1].tofile(output_path)
    _emit_log(log_cb, f"Clean background saved to: {output_path}")
    
    return output_path

if __name__ == "__main__":
    import json, sys
    
    img_path = sys.argv[1] if len(sys.argv) > 1 else "test/Slide2.JPG"
    json_path = sys.argv[2] if len(sys.argv) > 2 else "pptx-project/ocr_data.json"
    out_path = sys.argv[3] if len(sys.argv) > 3 else "pptx-project/clean_bg.png"
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    inpaint_background(img_path, data['text_data'], out_path)
