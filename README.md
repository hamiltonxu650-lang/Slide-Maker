# Slide Maker

[English](README.md) | [简体中文](README.zh-CN.md)

Slide Maker is an offline desktop tool for turning PDFs, screenshots, and slide images into editable PowerPoint presentations. It is designed for local-first workflows where privacy, layout fidelity, and clean background reconstruction matter more than cloud automation.

The current build combines OCR, text cleanup, background inpainting, and PPTX reconstruction into a Windows-focused desktop app with a CLI fallback.

## Features

- Convert PDF pages into editable `.pptx` slides
- Convert screenshots or image folders into editable presentations
- Rebuild text boxes with OCR-based positions, colors, and sizing
- Remove original text from the background before rebuilding slides
- Prefer lightweight OCR backends for local packaging
- Run fully offline after dependencies are installed
- Provide both desktop UI and command-line workflows

## How It Works

Slide Maker uses a multi-stage local pipeline:

1. Extract pages from a PDF or collect input images
2. Run OCR to detect text, boxes, and reading order
3. Estimate font size and sample text color from the source image
4. Remove source text from the page background using inpainting
5. Reconstruct editable slides as `.pptx`

The repository currently uses:

- `RapidOCR` as the preferred OCR backend
- Windows OCR as a fallback on supported systems
- `simple-lama-inpainting` plus OpenCV fallback for background cleanup
- `python-pptx` for PowerPoint generation
- `PyQt6` for the desktop app

## Requirements

- Python 3.10+ recommended
- Windows is the primary target for the desktop build
- PowerShell for the packaging script
- Local Python environment with the packages in `requirements.txt`

## Installation

Create a virtual environment and install dependencies:

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

If you only want to run the code without packaging, this is usually enough.

### Optional LaMa Model

This repository no longer treats the LaMa weight as a bundled source asset and does not rely on a hard-coded in-repo model path.

If you want AI background repair, download `big-lama.pt` yourself and place it in one of these locations:

- the reserved slot: `.slide_maker_data/models/lama/big-lama.pt`
- a custom path pointed to by `SLIDE_MAKER_LAMA_MODEL`

If no LaMa model is present, Slide Maker falls back to OpenCV Telea for background cleanup.

### Optional OCR Models

Slide Maker can also use user-supplied RapidOCR ONNX models instead of relying only on the packaged defaults.

Reserved OCR slot directory:

- `.slide_maker_data/models/rapidocr/onnxruntime/`

Expected filenames:

- `ch_PP-OCRv4_det_infer.onnx`
- `ch_ppocr_mobile_v2.0_cls_infer.onnx`
- `ch_PP-OCRv4_rec_infer.onnx`

Custom path environment variables:

- `SLIDE_MAKER_OCR_DET_MODEL`
- `SLIDE_MAKER_OCR_CLS_MODEL`
- `SLIDE_MAKER_OCR_REC_MODEL`

Quick download into the reserved slot:

```bash
python scripts/download_ocr_models.py
```

## Quick Start

### Terminal UI

If you want a guided cross-platform terminal workflow, launch:

```bash
python terminal_ui.py
```

The terminal UI works on Windows, macOS, and Linux without an additional TUI framework. It can:

- check the runtime environment
- guide model setup from scratch
- download the official OCR ONNX models into the reserved slot
- configure defaults for conversion
- run PDF / image / image-folder conversions interactively

### Desktop App

Launch the PyQt app:

```bash
python ui_app.py
```

The current UI supports two real workflows:

- PDF to PPTX
- Image to PPTX

### CLI

Run the higher-level conversion entrypoint:

```bash
python run_pipeline.py input.pdf --output Result_Presentation.pptx
```

Or convert an image or image folder:

```bash
python run_pipeline.py input.png --output Result_Presentation.pptx
python run_pipeline.py path\to\image_folder --output Result_Presentation.pptx
```

### Lower-Level Script

The original lower-level pipeline is still available:

```bash
python main.py --input path\to\images --output output.pptx
```

## Packaging

This repo includes a Windows packaging script based on PyInstaller:

```powershell
powershell -ExecutionPolicy Bypass -File build.ps1
```

The build script packages:

- the PyQt desktop app
- OCR runtime dependencies
- inpainting assets
- Node-based layout assets under `pptx-project`
- icons and runtime helpers

## Project Structure

```text
.
├── ui_app.py                    # Desktop app entrypoint
├── run_pipeline.py              # CLI conversion entrypoint
├── main.py                      # Core image-to-ppt pipeline
├── ocr_engine.py                # OCR backend adapter
├── image_processor.py           # Text mask creation and background cleanup
├── ppt_generator.py             # PPTX reconstruction
├── extract_pdf.py               # PDF page extraction
├── services/                    # Conversion orchestration and app models
├── ui/                          # PyQt UI components
├── assets/                      # Icons and bundled visuals
├── pptx-project/                # Supplemental layout engine assets
├── build.ps1                    # Windows build script
└── requirements.txt
```

## Output

The result is an editable `.pptx` presentation. Depending on OCR and cleanup availability, output may be:

- fully reconstructed with editable text boxes
- partially reconstructed with cleaner text layout
- compatibility-oriented image-based slides when OCR runtime is unavailable

## Status

This repository is an actively iterated local product/workbench rather than a polished public SDK. You will also find development logs and architecture notes in the repo, which are useful for deeper context but are not required for normal usage.

## License

No dedicated README license section was present before this file was added. Review the repository contents and any future license file before commercial or public redistribution.
