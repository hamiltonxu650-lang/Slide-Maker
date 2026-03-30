import cv2
import numpy as np
from ocr_engine import extract_text_data
from utils import extract_text_color
from image_processor import create_smart_text_mask

img_path = r"d:\maker\test\extracted_slides\slide_011.png"
img = cv2.imdecode(np.fromfile(img_path, dtype=np.uint8), cv2.IMREAD_COLOR)

text_data = extract_text_data(img_path)
print(f"Detected {len(text_data)} text boxes on Slide 11.")

gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
h, w = img.shape[:2]

for td in text_data:
    box = td['box']
    td['color'] = extract_text_color(img, box)
    tr, tg, tb = td['color']
    
    pts = np.array(box, dtype=np.int32)
    x, y, bw, bh = cv2.boundingRect(pts)
    
    pad = 6
    y1, y2 = max(0, y - pad), min(h, y + bh + pad)
    x1, x2 = max(0, x - pad), min(w, x + bw + pad)
    
    border_vals = []
    if y1 > 0: border_vals.extend(gray[max(0, y1-3):y1, x1:x2].flatten())
    if y2 < h: border_vals.extend(gray[y2:min(h, y2+3), x1:x2].flatten())
    bg_bright = np.median(border_vals) if border_vals else 127
    txt_bright = 0.299*tr + 0.587*tg + 0.114*tb
    
    print(f"[{td['text'][:15]:<15}] BG: {bg_bright:.1f} | TXT: {txt_bright:.1f} | IsBrighter: {txt_bright > bg_bright}")

mask = create_smart_text_mask(img, text_data)
cv2.imwrite("mask_debug_11.png", mask)
print("Saved mask_debug_11.png")
