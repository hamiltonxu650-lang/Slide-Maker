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
