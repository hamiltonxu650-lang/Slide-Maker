import cv2
import numpy as np


def order_points(pts):
    """
    Orders the points in the following order:
    Top-Left, Top-Right, Bottom-Right, Bottom-Left
    """
    rect = np.zeros((4, 2), dtype="float32")
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]

    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]

    return rect


def four_point_transform(image, pts):
    """
    Computes the perspective transform of the region of interest
    defined by the 4 points (pts) in the image.
    """
    rect = order_points(pts)
    (tl, tr, br, bl) = rect

    # compute the width of the new image
    widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
    widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
    maxWidth = max(int(widthA), int(widthB))

    # compute the height of the new image
    heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
    heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
    maxHeight = max(int(heightA), int(heightB))

    # destination points
    dst = np.array([
        [0, 0],
        [maxWidth - 1, 0],
        [maxWidth - 1, maxHeight - 1],
        [0, maxHeight - 1]
    ], dtype="float32")

    # calculate transform matrix
    M = cv2.getPerspectiveTransform(rect, dst)
    warped = cv2.warpPerspective(image, M, (maxWidth, maxHeight))

    return warped


def enhance_scanned_document(image: np.ndarray, mode: str = "color_enhance") -> np.ndarray:
    """
    Apply CamScanner-style enhancement to a cropped document image.
    
    Core technique: Gaussian-division illumination normalization
    (原图 ÷ 大核高斯模糊 = 去除不均匀光照, 保留文字细节)
    
    Modes:
      - "color_enhance": Keep color, normalize lighting, gentle sharpen (default)
      - "bw_clean":      Black-and-white adaptive threshold scan
      - "gray_sharp":    Grayscale with sharpening
    """
    if image is None or image.size == 0:
        return image

    h, w = image.shape[:2]

    if mode == "bw_clean":
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        # Denoise lightly
        gray = cv2.medianBlur(gray, 3)
        # Adaptive threshold for clean B&W
        block_size = max(11, (min(h, w) // 40) | 1)
        binary = cv2.adaptiveThreshold(
            gray, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            block_size, 5
        )
        return cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR)

    elif mode == "gray_sharp":
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        # Gaussian division: remove uneven lighting
        kernel_size = max(h, w) // 8
        if kernel_size % 2 == 0:
            kernel_size += 1
        kernel_size = max(kernel_size, 51)
        blur = cv2.GaussianBlur(gray, (kernel_size, kernel_size), 0)
        normalized = cv2.divide(gray, blur, scale=255) # Scale to pure white
        # Sharpen
        sharpening_kernel = np.array([
            [0, -0.6, 0],
            [-0.6, 3.4, -0.6],
            [0, -0.6, 0]
        ], dtype=np.float32)
        sharpened = cv2.filter2D(normalized, -1, sharpening_kernel)
        sharpened = np.clip(sharpened, 0, 255).astype(np.uint8)
        return cv2.cvtColor(sharpened, cv2.COLOR_GRAY2BGR)

    else:
        # color_enhance: 保留原图色彩和光照，仅提升清晰度 (Unsharp Masking)
        # 完全不改变背景颜色和全局亮度，只是让文字变得锐利
        
        # 1. 轻微降噪，防止锐化时放大噪点
        denoised = cv2.fastNlMeansDenoisingColored(image, None, 3, 3, 7, 21)
        
        # 2. Unsharp Masking (USM) 锐化
        # 原理: 原图 + (原图 - 模糊图) * 强度
        # 这样只在边缘（文字）处产生对比度增强，不会改变大面积的底色
        blur = cv2.GaussianBlur(denoised, (0, 0), 2.0)
        
        # alpha=1.5, beta=-0.5 意味着将边缘对比度提升 50%
        result = cv2.addWeighted(denoised, 1.5, blur, -0.5, 0)
        
        return result


def _fallback_corners(image: np.ndarray) -> np.ndarray:
    h, w = image.shape[:2]
    padding_x = int(w * 0.05)
    padding_y = int(h * 0.05)
    return np.array([
        [padding_x, padding_y],
        [w - 1 - padding_x, padding_y],
        [w - 1 - padding_x, h - 1 - padding_y],
        [padding_x, h - 1 - padding_y]
    ], dtype=np.float32)


def detect_document_corners(image: np.ndarray) -> np.ndarray:
    """
    Returns the [4, 2] coordinates of the document boundary.
    If not found, returns the 4 corners of the full image (with a slight padding for UI dragging).
    """
    ratio = image.shape[0] / 500.0

    new_h = 500
    new_w = int(image.shape[1] / ratio)
    if new_h <= 0 or new_w <= 0:
        return _fallback_corners(image)

    image_resized = cv2.resize(image, (new_w, new_h))

    gray = cv2.cvtColor(image_resized, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (5, 5), 0)
    edged = cv2.Canny(gray, 75, 200)

    cnts, _ = cv2.findContours(edged.copy(), cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    cnts = sorted(cnts, key=cv2.contourArea, reverse=True)[:5]

    screenCnt = None
    img_area = new_h * new_w

    for c in cnts:
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.02 * peri, True)
        if len(approx) == 4:
            area = cv2.contourArea(c)
            if area > img_area * 0.15:
                screenCnt = approx
                break

    if screenCnt is None:
        return _fallback_corners(image)

    return (screenCnt.reshape(4, 2) * ratio).astype(np.float32)


def scan_document(image: np.ndarray, log_cb=None, enhance_mode: str = "color_enhance") -> np.ndarray:
    """
    Full scan pipeline: detect corners -> perspective crop -> enhance.
    Auto scanner entry point for CLI / pipeline.
    """
    orig = image.copy()
    pts = detect_document_corners(image)

    fallback = _fallback_corners(image)
    if np.allclose(pts, fallback, atol=1.0):
        if log_cb:
            log_cb("[Scanner] 无法检测到边界清晰的4角文档轮廓，仅执行增强处理。")
        enhanced = enhance_scanned_document(orig, mode=enhance_mode)
        return enhanced

    if log_cb:
        log_cb("[Scanner] 成功检测到斜拍文档轮廓，执行透视修正 + 画质增强。")

    warped = four_point_transform(orig, pts)
    enhanced = enhance_scanned_document(warped, mode=enhance_mode)
    return enhanced
