import argparse
import os
from pathlib import Path

import cv2

from ppt_generator import PPTGenerator
from utils import estimate_font_size, extract_text_color


DEFAULT_OCR_MAX_LONG_EDGE = 3200


def _emit_log(log_cb, message):
    if log_cb:
        log_cb(message)
    else:
        print(message)


def _build_ocr_input(img_path, cv_img, working_dir, index, log_cb, options):
    ocr_max_long_edge = int(options.get("ocr_max_long_edge", DEFAULT_OCR_MAX_LONG_EDGE) or 0)
    if ocr_max_long_edge <= 0:
        return img_path, 1.0

    img_h, img_w = cv_img.shape[:2]
    longest_edge = max(img_w, img_h)
    if longest_edge <= ocr_max_long_edge:
        return img_path, 1.0

    resize_scale = float(ocr_max_long_edge) / float(longest_edge)
    resized = cv2.resize(
        cv_img,
        (max(1, int(round(img_w * resize_scale))), max(1, int(round(img_h * resize_scale)))),
        interpolation=cv2.INTER_AREA,
    )
    ocr_input_path = os.path.join(working_dir, f"ocr_input_{index}.png")
    cv2.imencode(".png", resized)[1].tofile(ocr_input_path)
    _emit_log(
        log_cb,
        f"[*] OCR analysis image resized to {resized.shape[1]}x{resized.shape[0]} for faster recognition.",
    )
    return ocr_input_path, (1.0 / resize_scale)


def _scale_text_data(text_data, scale_factor):
    if abs(scale_factor - 1.0) < 1e-6:
        return text_data

    scaled = []
    for td in text_data:
        item = dict(td)
        item["box"] = [
            [float(point[0]) * scale_factor, float(point[1]) * scale_factor]
            for point in td["box"]
        ]
        item["height"] = float(td.get("height", 0.0)) * scale_factor
        item["width"] = float(td.get("width", 0.0)) * scale_factor
        scaled.append(item)
    return scaled


def process_images_to_ppt(
    input_dir_or_file,
    output_ppt="output.pptx",
    slide_progress_cb=None,
    log_cb=None,
    options=None,
    working_dir=None,
):
    options = dict(options or {})
    cleanup_options = dict(options.get("cleanup_options", {}))
    font_scale = float(options.get("font_scale", 1.0))
    box_scale = float(options.get("box_scale", 1.5))
    canvas_dpi = float(options.get("canvas_dpi", 96))
    working_dir = os.path.abspath(working_dir or "pptx-project")
    os.makedirs(working_dir, exist_ok=True)

    images = []
    if os.path.isdir(input_dir_or_file):
        images = [
            str(path)
            for path in sorted(Path(input_dir_or_file).iterdir())
            if path.is_file() and path.suffix.lower() in {".png", ".jpg", ".jpeg"}
        ]
    else:
        images = [input_dir_or_file]

    if not images:
        raise FileNotFoundError("No images found to process.")

    total_images = len(images)
    _emit_log(log_cb, f"Found {total_images} images to process.")
    if slide_progress_cb:
        slide_progress_cb(0, total_images, "准备 OCR 与背景修复")

    from ocr_engine import extract_text_data, get_ocr_runtime_status

    ocr_status = get_ocr_runtime_status()
    if ocr_status["available"]:
        backend = ocr_status.get("backend") or "unknown"
        _emit_log(log_cb, f"[*] OCR backend: {backend}")
        model_message = str(ocr_status.get("model_message") or "").strip()
        if model_message:
            _emit_log(log_cb, f"[*] {model_message}")
    else:
        _emit_log(
            log_cb,
            "[!] OCR runtime unavailable. Slides will be exported as image-based PPTX pages.",
        )

    ppt = PPTGenerator()
    all_slides = []

    for i, img_path in enumerate(images):
        _emit_log(log_cb, f"Processing slide {i + 1}/{total_images}: {img_path}")
        if slide_progress_cb:
            slide_progress_cb(i, total_images, f"正在处理第 {i + 1}/{total_images} 页")

        import numpy as np

        cv_img = cv2.imdecode(np.fromfile(img_path, dtype=np.uint8), cv2.IMREAD_COLOR)
        if cv_img is None:
            raise FileNotFoundError(f"Cannot read image: {img_path}")
            
        if options.get("enable_document_scanner"):
            from scanner_engine import scan_document
            cv_img = scan_document(cv_img, log_cb=log_cb)

        img_h, img_w = cv_img.shape[:2]

        # Set slide dimensions for every slide to match its actual image
        canvas_scale = ppt.set_slide_dimensions(img_w, img_h, dpi=canvas_dpi)
        if canvas_scale < 1.0:
            _emit_log(
                log_cb,
                f"[*] Slide canvas exceeded PowerPoint size limits; scaled to {canvas_scale:.4f}x.",
            )

        ocr_input_path, ocr_scale_factor = _build_ocr_input(
            img_path,
            cv_img,
            working_dir,
            i,
            log_cb,
            options,
        )
        text_data = _scale_text_data(list(extract_text_data(ocr_input_path, log_cb=log_cb)), ocr_scale_factor)
        for td in text_data:
            box = td["box"]
            td["font_size"] = estimate_font_size(td["height"], scale=font_scale)
            td["color"] = extract_text_color(cv_img, box)
            td["pptx_box_scale"] = box_scale
            td["pptx_font_scale"] = float(options.get("font_scale", 1.0))

        from image_processor import inpaint_background

        clean_bg_filename = f"clean_bg_{i}.png"
        clean_bg_path = os.path.join(working_dir, clean_bg_filename)
        inpaint_background(
            img_path,
            text_data,
            clean_bg_path,
            cleanup_options=cleanup_options,
            log_cb=log_cb,
        )

        ppt.add_slide(clean_bg_path, text_data, dpi=canvas_dpi)

        all_slides.append(
            {
                "width": img_w,
                "height": img_h,
                "text_data": text_data,
                "background_image": clean_bg_path,
            }
        )

    import json

    json_output = os.path.join(working_dir, "ocr_data.json")
    with open(json_output, "w", encoding="utf-8") as f:
        json.dump(all_slides, f, ensure_ascii=False)
    _emit_log(log_cb, f"Dumped multi-slide layout data to {json_output}")

    ppt.save(output_ppt)
    _emit_log(log_cb, f"Successfully saved editable presentation (Python version) to: {output_ppt}")
    if slide_progress_cb:
        slide_progress_cb(total_images, total_images, "幻灯片数据处理完成")

    return {
        "slides_processed": total_images,
        "ocr_data_path": os.path.abspath(json_output),
        "output_path": os.path.abspath(output_ppt),
        "ocr_runtime_available": bool(ocr_status["available"]),
        "ocr_runtime_error": str(ocr_status.get("error") or ""),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Convert NotebookLM Screenshots to Editable PPT using OCR and LaMa"
    )
    parser.add_argument("--input", required=True, help="Path to input image or directory of images")
    parser.add_argument("--output", default="output.pptx", help="Path to output .pptx file")

    args = parser.parse_args()
    process_images_to_ppt(args.input, args.output)
