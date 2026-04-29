import os
import sys
from math import sqrt

try:
    import fitz  # PyMuPDF
except ModuleNotFoundError:  # pragma: no cover - packaged fallback
    import pymupdf as fitz


DEFAULT_MAX_RENDER_PIXELS = 10_000_000
DEFAULT_MAX_RENDER_EDGE = 5000


def _emit_log(log_cb, message):
    if log_cb:
        log_cb(message)
    else:
        print(message)


def _safe_render_scale(page, requested_dpi, max_pixels, max_edge):
    requested_dpi = max(24, int(requested_dpi or 200))
    scale = requested_dpi / 72.0
    width = max(1.0, float(page.rect.width) * scale)
    height = max(1.0, float(page.rect.height) * scale)

    limit_factor = 1.0
    if max_pixels and width * height > max_pixels:
        limit_factor = min(limit_factor, sqrt(float(max_pixels) / float(width * height)))
    if max_edge and max(width, height) > max_edge:
        limit_factor = min(limit_factor, float(max_edge) / float(max(width, height)))

    safe_scale = max(0.1, scale * limit_factor)
    render_w = int(round(float(page.rect.width) * safe_scale))
    render_h = int(round(float(page.rect.height) * safe_scale))
    return safe_scale, safe_scale * 72.0, render_w, render_h


def extract_pdf_to_images(
    pdf_path,
    out_dir,
    dpi=200,
    progress_cb=None,
    log_cb=None,
    max_pixels=DEFAULT_MAX_RENDER_PIXELS,
    max_edge=DEFAULT_MAX_RENDER_EDGE,
):
    _emit_log(log_cb, f"Opening PDF: {pdf_path}")
    doc = fitz.open(pdf_path)
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    try:
        total_pages = len(doc)
        for i in range(total_pages):
            _emit_log(log_cb, f"Extracting PDF page {i + 1}/{total_pages}...")
            page = doc.load_page(i)
            scale, effective_dpi, render_w, render_h = _safe_render_scale(page, dpi, max_pixels, max_edge)
            if effective_dpi < float(dpi) - 0.5:
                _emit_log(
                    log_cb,
                    (
                        "[!] PDF page is very large; rendering at "
                        f"{effective_dpi:.0f} DPI ({render_w}x{render_h}) instead of {int(dpi)} DPI "
                        "to avoid exhausting memory."
                    ),
                )
            pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale), colorspace=fitz.csRGB, alpha=False)
            out_file = os.path.join(out_dir, f"page_{i+1:03d}.png")
            pix.save(out_file)
            pix = None
            _emit_log(log_cb, f"  Saved {out_file}")
            if progress_cb:
                progress_cb(i + 1, total_pages, out_file)
    finally:
        doc.close()


if __name__ == "__main__":
    pdf_file = sys.argv[1] if len(sys.argv) > 1 else "test/Quiz 1.pdf"
    out_dir = sys.argv[2] if len(sys.argv) > 2 else "test/extracted_quiz1"
    extract_pdf_to_images(pdf_file, out_dir)
