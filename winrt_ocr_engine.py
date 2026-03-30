import asyncio
from winrt.windows.media.ocr import OcrEngine
from winrt.windows.graphics.imaging import BitmapDecoder
from winrt.windows.storage import StorageFile
import os

async def run_ocr(image_path):
    # StorageFile requires absolute path
    abs_path = os.path.abspath(image_path)
    file = await StorageFile.get_file_from_path_async(abs_path)
    stream = await file.open_async(0) 
    
    decoder = await BitmapDecoder.create_async(stream)
    software_bitmap = await decoder.get_software_bitmap_async()
    
    engine = OcrEngine.try_create_from_user_profile_languages()
    if not engine:
        print("No OCR Engine available for user profile languages.")
        return []

    result = await engine.recognize_async(software_bitmap)
    
    extracted_data = []
    
    for line in result.lines:
        text = line.text
        if not line.words: continue
        
        x_min = min(w.bounding_rect.x for w in line.words)
        y_min = min(w.bounding_rect.y for w in line.words)
        x_max = max((w.bounding_rect.x + w.bounding_rect.width) for w in line.words)
        y_max = max((w.bounding_rect.y + w.bounding_rect.height) for w in line.words)
        
        box = [
            [x_min, y_min],
            [x_max, y_min],
            [x_max, y_max],
            [x_min, y_max]
        ]
        
        extracted_data.append({
            'box': box,
            'text': text,
            'confidence': 1.0,
            'height': y_max - y_min,
            'width': x_max - x_min
        })
        
    return extracted_data

def extract_text_data(image_path):
    return asyncio.run(run_ocr(image_path))

if __name__ == "__main__":
    import sys
    test_file = sys.argv[1] if len(sys.argv) > 1 else "test/test_image.jpg"
    res = extract_text_data(test_file)
    for r in res:
        print(r)
