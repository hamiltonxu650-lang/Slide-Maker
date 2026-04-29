import os
import sys

try:
    import fitz  # PyMuPDF
except ModuleNotFoundError:  # pragma: no cover - packaged fallback
    import pymupdf as fitz


DEFAULT_MAX_RENDER_PIXELS = 6_000_000
DEFAULT_MAX_RENDER_EDGE = 3200


class PdfRenderCompatibilityError(RuntimeError):
    pass


def _emit_log(log_cb, message):
    if log_cb:
        log_cb(message)
    else:
        print(message)


def _render_plan(page, requested_dpi):
    requested_dpi = max(24, int(requested_dpi or 200))
    scale = requested_dpi / 72.0
    render_w = max(1, int(round(float(page.rect.width) * scale)))
    render_h = max(1, int(round(float(page.rect.height) * scale)))
    return scale, render_w, render_h


def _validate_render_compatibility(page_number, dpi, render_w, render_h, max_pixels, max_edge):
    pixels = render_w * render_h
    problems = []
    if max_pixels and pixels > max_pixels:
        problems.append(f"像素量 {pixels:,} 超过安全上限 {int(max_pixels):,}")
    if max_edge and max(render_w, render_h) > max_edge:
        problems.append(f"最长边 {max(render_w, render_h):,}px 超过安全上限 {int(max_edge):,}px")

    if not problems:
        return

    raise PdfRenderCompatibilityError(
        "PDF 页面与当前高质量转换设置不兼容："
        f"第 {page_number} 页按 {int(dpi)} DPI 会渲染为 {render_w:,}x{render_h:,}px，"
        + "，".join(problems)
        + "。为保证输出质量，Slide Maker 不会自动降低 DPI 或缩小页面；"
        "请先裁掉 PDF 的超大空白画布、拆分异常页面，或换用页面尺寸正常的 PDF 后再转换。"
    )


def _color_int_to_rgb(color_value):
    color_value = int(color_value or 0)
    return [
        (color_value >> 16) & 255,
        (color_value >> 8) & 255,
        color_value & 255,
    ]


def extract_pdf_native_text_data(pdf_path, dpi=200, log_cb=None):
    doc = fitz.open(pdf_path)
    scale = max(24, int(dpi or 200)) / 72.0
    pages = {}
    try:
        for page_index in range(len(doc)):
            page = doc.load_page(page_index)
            page_key = f"page_{page_index + 1:03d}.png"
            text_items = []
            page_dict = page.get_text("dict")
            for block in page_dict.get("blocks", []):
                if block.get("type") != 0:
                    continue
                for line in block.get("lines", []):
                    spans = [span for span in line.get("spans", []) if str(span.get("text", "")).strip()]
                    if not spans:
                        continue
                    raw_text = "".join(str(span.get("text", "")) for span in spans).replace("\u00a0", " ")
                    text = " ".join(raw_text.split())
                    if not text:
                        continue

                    x0, y0, x1, y1 = line.get("bbox", spans[0].get("bbox", (0, 0, 0, 0)))
                    font_size = max(float(span.get("size", 0.0) or 0.0) for span in spans)
                    color = _color_int_to_rgb(spans[0].get("color", 0))
                    box = [
                        [x0 * scale, y0 * scale],
                        [x1 * scale, y0 * scale],
                        [x1 * scale, y1 * scale],
                        [x0 * scale, y1 * scale],
                    ]
                    text_items.append(
                        {
                            "text": text,
                            "box": box,
                            "height": (y1 - y0) * scale,
                            "width": (x1 - x0) * scale,
                            "color": color,
                            "font_size": max(font_size, 8.0),
                            "source": "pdf_native",
                        }
                    )
            pages[page_key] = text_items
            if text_items:
                _emit_log(log_cb, f"[*] Native PDF text extracted for page {page_index + 1}: {len(text_items)} lines.")
    finally:
        doc.close()
    return pages


def extract_pdf_to_images(
    pdf_path,
    out_dir,
    dpi=200,
    progress_cb=None,
    log_cb=None,
    control_cb=None,
    max_pixels=DEFAULT_MAX_RENDER_PIXELS,
    max_edge=DEFAULT_MAX_RENDER_EDGE,
):
    _emit_log(log_cb, f"Opening PDF: {pdf_path}")
    if control_cb:
        control_cb("提取页面", 15, "准备拆分 PDF 页面")
    doc = fitz.open(pdf_path)
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    try:
        total_pages = len(doc)
        for i in range(total_pages):
            if control_cb:
                control_cb("提取页面", 15, f"等待提取第 {i + 1}/{total_pages} 页")
            _emit_log(log_cb, f"Extracting PDF page {i + 1}/{total_pages}...")
            page = doc.load_page(i)
            scale, render_w, render_h = _render_plan(page, dpi)
            _validate_render_compatibility(i + 1, dpi, render_w, render_h, max_pixels, max_edge)
            pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale), colorspace=fitz.csRGB, alpha=False)
            out_file = os.path.join(out_dir, f"page_{i+1:03d}.png")
            pix.save(out_file)
            pix = None
            _emit_log(log_cb, f"  Saved {out_file}")
            if progress_cb:
                progress_cb(i + 1, total_pages, out_file)
            if control_cb:
                control_cb("提取页面", 15 + int(((i + 1) / max(total_pages, 1)) * 15), f"已提取第 {i + 1}/{total_pages} 页")
    finally:
        doc.close()


if __name__ == "__main__":
    pdf_file = sys.argv[1] if len(sys.argv) > 1 else "test/Quiz 1.pdf"
    out_dir = sys.argv[2] if len(sys.argv) > 2 else "test/extracted_quiz1"
    extract_pdf_to_images(pdf_file, out_dir)
