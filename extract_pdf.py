import os
import sys

try:
    import fitz  # PyMuPDF
except ModuleNotFoundError:  # pragma: no cover - packaged fallback
    import pymupdf as fitz


def _emit_log(log_cb, message):
    if log_cb:
        log_cb(message)
    else:
        print(message)


def extract_pdf_to_images(pdf_path, out_dir, dpi=200, progress_cb=None, log_cb=None):
    _emit_log(log_cb, f"Opening PDF: {pdf_path}")
    doc = fitz.open(pdf_path)
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    total_pages = len(doc)
    for i in range(total_pages):
        _emit_log(log_cb, f"Extracting PDF page {i + 1}/{total_pages}...")
        page = doc.load_page(i)
        scale = dpi / 72
        pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale), colorspace=fitz.csRGB, alpha=False)
        out_file = os.path.join(out_dir, f"page_{i+1:03d}.png")
        pix.save(out_file)
        _emit_log(log_cb, f"  Saved {out_file}")
        if progress_cb:
            progress_cb(i + 1, total_pages, out_file)


if __name__ == "__main__":
    pdf_file = sys.argv[1] if len(sys.argv) > 1 else "test/Quiz 1.pdf"
    out_dir = sys.argv[2] if len(sys.argv) > 2 else "test/extracted_quiz1"
    extract_pdf_to_images(pdf_file, out_dir)
