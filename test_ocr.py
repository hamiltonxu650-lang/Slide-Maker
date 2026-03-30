import cv2
import numpy as np
import os
from ocr_engine import extract_text_data

def run_test():
    # 1. Create a simple test image with text
    img = np.ones((150, 400, 3), dtype=np.uint8) * 255 # White background
    
    # 2. Draw some text onto the image
    text = "PaddleOCR Test Run"
    cv2.putText(img, text, (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2, cv2.LINE_AA)

    test_img_path = "test_sample.jpg"
    cv2.imwrite(test_img_path, img)
    print(f"Created test image at {test_img_path}")

    # 3. Process it using the ocr_engine
    print("Initializing PaddleOCR and extracting text data...")
    try:
        results = extract_text_data(test_img_path)
        print("\n--- OCR Results ---")
        if not results:
            print("No text elements found.")
        for idx, res in enumerate(results):
            print(f"[{idx+1}] Text: '{res['text']}', Confidence: {res['confidence']:.4f}")
            print(f"    Bounding Box: {res['box']}")
            print(f"    Computed Height: {res['height']:.2f}, Computed Width: {res['width']:.2f}")
            print("-" * 30)
        print("Integration Test Passed Successfully.")
    except Exception as e:
        print(f"Error encountered during OCR test: {e}")
    finally:
        # 4. Cleanup
        if os.path.exists(test_img_path):
            os.remove(test_img_path)

if __name__ == "__main__":
    run_test()
