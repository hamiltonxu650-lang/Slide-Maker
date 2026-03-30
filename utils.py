import cv2
import numpy as np
from PIL import Image
from collections import Counter

def create_mask_from_boxes(image_size, boxes, padding=5):
    """
    Creates a binary mask given the image size and a list of PaddleOCR bounding boxes.
    Boxes is a list of [[x1,y1],[x2,y2],[x3,y3],[x4,y4]]
    """
    mask = np.zeros((image_size[1], image_size[0]), dtype=np.uint8)
    for box in boxes:
        pts = np.array(box, dtype=np.int32)
        # Add slight padding to the text box to cover anti-aliased edges
        x, y, w, h = cv2.boundingRect(pts)
        cv2.rectangle(mask, (max(0, x-padding), max(0, y-padding)), (min(image_size[0], x+w+padding), min(image_size[1], y+h+padding)), 255, -1)
    
    # Convert numpy mask back to PIL image for Lama
    return Image.fromarray(mask)

def extract_text_color(image_cv, box):
    """
    Given a cv2 image and a bounding box, extract the actual text color.
    Uses K-means clustering to separate text pixels from background pixels,
    then picks the cluster that is furthest from the border background color.
    """
    pts = np.array(box, dtype=np.int32)
    x, y, w, h = cv2.boundingRect(pts)
    roi_bgr = image_cv[max(0, y):min(image_cv.shape[0], y+h), max(0, x):min(image_cv.shape[1], x+w)]
    
    if roi_bgr.size == 0:
        return (255, 255, 255)
    
    # Sample the border around this box to know the background color
    img_h, img_w = image_cv.shape[:2]
    border = 6
    border_pixels_list = []
    # Top strip
    t_y1, t_y2 = max(0, y - border), y
    if t_y2 > t_y1:
        # Gather border pixels (they are almost guaranteed to be background)
        border_pixels_list.append(image_cv[t_y1:t_y2, max(0,x):min(img_w,x+w)].reshape(-1, 3))
    # Bottom strip (original code had this, but the instruction snippet removed it. Re-adding for completeness if it was an oversight)
    b_y1, b_y2 = y+h, min(img_h, y+h+border)
    if b_y2 > b_y1:
        border_pixels_list.append(image_cv[b_y1:b_y2, max(0,x):min(img_w,x+w)].reshape(-1, 3))

    if h > 0 and w > 0:
        top = roi_bgr[0, :].reshape(-1, 3)
        bottom = roi_bgr[-1, :].reshape(-1, 3)
        left = roi_bgr[:, 0].reshape(-1, 3)
        right = roi_bgr[:, -1].reshape(-1, 3)
        border_pixels_list.extend([top, bottom, left, right])
    
    if border_pixels_list:
        border_pixels = np.vstack(border_pixels_list)
    else:
        border_pixels = np.empty((0, 3))
        
    bg_color_guess = np.median(border_pixels, axis=0) if border_pixels.shape[0] > 0 else np.array([255, 255, 255])
    
    # K-Means clustering to find 2 dominant colors
    pixels = np.float32(roi_bgr.reshape(-1, 3))
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
    _, labels, centers = cv2.kmeans(pixels, 2, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
    
    c0 = centers[0]
    c1 = centers[1]
    
    # The text color is the cluster center FARTHEST from the border background color
    dist0 = np.sum(np.abs(c0 - bg_color_guess))
    dist1 = np.sum(np.abs(c1 - bg_color_guess))
    
    # Return the color that is most different from the background border
    text_color = c0 if dist0 > dist1 else c1
    return [int(c) for c in text_color]

def estimate_font_size(box_height, scale=1.0):
    """
    Simple heuristic to map pixel height to point size.
    You might need to adjust the factor based on actual DPI/Resolution.
    Typically, 1 point = 1.33 pixels. So pt = pixels * 0.75
    """
    return int(max(box_height * 0.75 * scale, 8.0))
