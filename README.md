# Slide Maker

[English](README.md) | [简体中文](README.zh-CN.md)

Slide Maker is a local-first toolchain for rebuilding PDFs, screenshots, and slide images into editable PowerPoint presentations.

`v0.2.0` is the first version that brings the current product shape together:

- a cross-platform guided `terminal_ui.py`
- a desktop UI for day-to-day use
- a CLI for scripted runs
- user-managed LaMa and OCR model slots
- a high-fidelity Node layout pass with compatibility fallback

## What This Version Does

Slide Maker can:

- convert PDF files into editable `.pptx`
- convert a single image into `.pptx`
- convert a directory of images into a multi-slide `.pptx`
- rebuild text boxes from OCR results
- remove source text from the background before reconstruction
- stay fully local after dependencies and optional models are ready

The current pipeline is:

1. extract PDF pages or collect input images
2. run OCR and detect text boxes
3. estimate font size and sample text color from the source
4. clean the background with LaMa or OpenCV fallback
5. generate an editable `.pptx`
6. optionally run a Node-based high-fidelity layout pass

## Platform Support

| Workflow | Windows | macOS | Linux | Notes |
| --- | --- | --- | --- | --- |
| Terminal UI | Yes | Yes | Yes | Recommended starting point |
| CLI | Yes | Yes | Yes | Good for automation |
| Desktop UI from source | Yes | Yes | Yes | Requires PyQt6 dependencies |
| Packaged desktop build | Yes | No | No | Current packaging script targets Windows |

## Requirements

- Python 3.10 or newer
- Node.js on `PATH` if you want the high-fidelity layout engine
- Packages from `requirements.txt`
- `npm install` inside `pptx-project`
- PowerShell only when building the Windows packaged app

If Node.js is not available, Slide Maker still runs and falls back to compatibility rendering.

## Setup

### Windows

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup_windows.ps1
```

### macOS

```bash
bash ./scripts/setup_macos.sh
```

### Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements.txt
cd pptx-project && npm install && cd ..
```

## Recommended Start: Terminal UI

The simplest way to configure and use this release is:

```bash
python terminal_ui.py
```

The terminal UI works on Windows, macOS, and Linux and can:

- inspect the runtime environment
- guide LaMa and OCR model setup from scratch
- download the official OCR ONNX models into the reserved slot
- open model directories for you
- save default conversion preferences
- run PDF, image, and image-directory conversions interactively

## Other Entry Points

### Desktop UI

```bash
python ui_app.py
```

Useful flags:

```bash
python ui_app.py --demo
```

### CLI

```bash
python run_pipeline.py input.pdf --output Result_Presentation.pptx
python run_pipeline.py input.png --output Result_Presentation.pptx
python run_pipeline.py ./slides --output Result_Presentation.pptx
```

Use `--no-open` if you do not want the app to prompt to open the result.

### Web App

If you want to run Slide Maker as a web app, start the FastAPI entrypoint:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-web.txt
cd pptx-project && npm install && cd ..
uvicorn web_app:app --host 0.0.0.0 --port 7860
```

Then open:

```text
http://127.0.0.1:7860
```

The web UI currently supports:

- PDF uploads
- PNG / JPG / JPEG uploads
- Conversion focus selection
- Direct `.pptx` download

### Lower-Level Pipeline

```bash
python main.py --input ./slides --output output.pptx
```

## Model Management

### LaMa Background-Repair Model

Slide Maker no longer treats the LaMa weight as a bundled repository asset.

Expected filename:

- `big-lama.pt`

Supported locations:

- reserved slot: `.slide_maker_data/models/lama/big-lama.pt`
- custom environment variable: `SLIDE_MAKER_LAMA_MODEL`
- compatibility alias: `LAMA_MODEL`

If LaMa is not configured, Slide Maker automatically falls back to OpenCV Telea.

Upstream model source used by the original dependency:

- [big-lama.pt](https://github.com/enesmsahin/simple-lama-inpainting/releases/download/v0.1.0/big-lama.pt)

### OCR Models

By default, Slide Maker can use the packaged RapidOCR models. This release also supports user-managed OCR models.

Reserved slot directory:

- `.slide_maker_data/models/rapidocr/onnxruntime/`

Expected filenames:

- `ch_PP-OCRv4_det_infer.onnx`
- `ch_ppocr_mobile_v2.0_cls_infer.onnx`
- `ch_PP-OCRv4_rec_infer.onnx`

Custom environment variables:

- `SLIDE_MAKER_OCR_DET_MODEL`
- `SLIDE_MAKER_OCR_CLS_MODEL`
- `SLIDE_MAKER_OCR_REC_MODEL`

Quick download into the reserved slot:

```bash
python scripts/download_ocr_models.py
```

## Rendering Modes

Slide Maker can finish in two ways:

- High fidelity: uses Node.js and `pptx-project/layout_engine.js` for better layout recovery
- Compatibility: keeps the Python-generated `.pptx` output when Node.js is unavailable or compatibility mode is selected

That means the tool remains usable even on a minimal setup.

## Runtime Data

At runtime, Slide Maker writes logs, temp files, and model slots into app data:

- source checkout on macOS/Linux: `.slide_maker_data/`
- Windows app-data mode: `%LOCALAPPDATA%\SlideMaker\`

Useful subdirectories include:

- `logs/`
- `runtime/`
- `models/lama/`
- `models/rapidocr/onnxruntime/`
- `config/`

## Packaging

Windows packaging is driven by:

- `build.ps1`
- `Slide_Maker.spec`

This release no longer packages the LaMa model as a repository-tracked source asset.

### Docker Deployment

The repository now also includes a Dockerfile for the web version, so it can be deployed to Docker-capable platforms such as Railway, Render, Fly.io, or a self-hosted server:

```bash
docker build -t slide-maker-web .
docker run --rm -p 7860:7860 slide-maker-web
```

## Project Layout

```text
.
├── terminal_ui.py               # Cross-platform guided terminal workflow
├── ui_app.py                    # Desktop UI entrypoint
├── run_pipeline.py              # High-level CLI entrypoint
├── main.py                      # Core image-to-ppt pipeline
├── services/                    # Settings, runtime detection, conversion orchestration
├── ui/                          # PyQt UI components
├── scripts/                     # Setup helpers and OCR download script
├── pptx-project/                # Node layout engine assets
├── assets/                      # Icons and bundled visuals
└── build.ps1                    # Windows packaging script
```

## Notes

- The repository is an actively iterated product workbench, not a polished public SDK.
- Some historical development logs are still kept in-tree for context.
- No dedicated license file is documented in the repository root yet. Review usage rights before redistribution.
