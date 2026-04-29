# Slide Maker

[English](README.md) | [简体中文](README.zh-CN.md)

Slide Maker is a local-first desktop tool for converting PDFs, screenshots, scans, and photographed slides into editable PowerPoint files.

## v0.4.0 Refresh

This refresh keeps the release line at `v0.4.0` and folds the Mac and Windows fixes back into the same version line instead of creating a new version number.

### Desktop UI

- Mac now has a dedicated desktop build and is treated as a first-class target.
- Windows uses the same redesigned frontend as the Mac build, while keeping Windows-specific chrome, font fallback, and file picker behavior.
- Blurry title-bar and sidebar icons were replaced with the high-resolution app asset.

### Conversion Flow

- Mac GUI launches now search app resources and common GUI-missing Node locations such as `~/.local/bin`, Homebrew, and NVM before falling back to compatibility mode.
- Packaged apps prefer bundled runtimes when available.

### PDF And Image Quality

- PDF conversion now passes the real page DPI into the Node layout engine.
- PDF text-based pages use the native PDF text layer before falling back to OCR.
- This fixes oversized text boxes, off-slide text, OCR word splitting, and garbled text in many text-based PDFs.
- PDF DPI choices are unified as `100 / 150 / 200 / 300 DPI`.
- Slide Maker does not silently lower a user-selected DPI.
- Oversized pages are rejected by compatibility preflight instead of being downsampled or pushed into a memory crash.
- Background repair requires LaMa and no longer silently falls back to OpenCV.
- PNG/image conversion was retested in a restricted GUI-like environment and still produced high-fidelity Node output.

## Download And Install

Use the files that are actually attached to the public GitHub release. Do not use GitHub's green `Code` button as an installer; that button is for source code, not the packaged app.

### Windows

The current public `v0.4.0` GitHub release includes a Windows portable package:

- [Slide-Maker-v0.4.0-windows-portable.zip](https://github.com/hamiltonxu650-lang/Slide-Maker/releases/download/v0.4.0/Slide-Maker-v0.4.0-windows-portable.zip)
- [Slide-Maker-v0.4.0-windows-portable.zip.sha256.txt](https://github.com/hamiltonxu650-lang/Slide-Maker/releases/download/v0.4.0/Slide-Maker-v0.4.0-windows-portable.zip.sha256.txt)

Install steps:

1. Open the [v0.4.0 release page](https://github.com/hamiltonxu650-lang/Slide-Maker/releases/tag/v0.4.0).
2. Expand `Assets`.
3. Download `Slide-Maker-v0.4.0-windows-portable.zip`.
4. Extract the package to any folder.
5. Run `SlideMaker.exe`.

The Windows portable package contains the visible PyInstaller GUI shell plus a portable worker runtime. The worker runtime includes portable Python, OCR dependencies, Node, the PPTX layout engine, and the LaMa model.

### Mac

The Mac desktop app has been prepared locally, but the public GitHub `v0.4.0` release does not currently include a Mac `.app` asset. Until a Mac package is attached to the GitHub release, Mac users should run the app from source:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements.txt
cd pptx-project && npm install && cd ..
python ui_app.py
```

## System Requirements

### Windows

- Windows 10 or Windows 11, 64-bit
- Intel or AMD x64 CPU
- 16 GB RAM for normal use
- 32 GB RAM recommended for larger PDFs
- 4 GB or more free disk space
- No GPU required
- No separate Python or Node.js installation required for the packaged portable build

### macOS

- macOS 10.13 or newer for the packaged Mac app
- Apple Silicon or Intel Mac supported by the bundled Python runtime
- 16 GB RAM recommended
- 4 GB or more free disk space

### Source Runtime

- Python 3.9 or newer
- Node.js for high-fidelity PPTX layout
- `pptx-project` dependencies installed with `npm install`
- LaMa model available as `big-lama.pt`
- PyQt6 for the desktop UI

## Quick Start From Source

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements.txt
cd pptx-project && npm install && cd ..
python ui_app.py
```

### Windows

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup_windows.ps1
python ui_app.py
```

## Other Entry Points

### Terminal UI

```bash
python terminal_ui.py
```

The terminal UI is useful for setup checks, model checks, and guided conversion.

### CLI

```bash
python run_pipeline.py input.pdf --output Result_Presentation.pptx
python run_pipeline.py input.png --output Result_Presentation.pptx
python run_pipeline.py ./slides --output Result_Presentation.pptx
python run_pipeline.py input.jpg --scan --output Result_Presentation.pptx
```

Use `--no-open` if you do not want the app to prompt to open the result.

### Web App

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-web.txt
cd pptx-project && npm install && cd ..
uvicorn web_app:app --host 0.0.0.0 --port 7860
```

Then open `http://127.0.0.1:7860`.

## Model Setup

### LaMa Background Repair

LaMa is required for background repair.

Expected filename:

- `big-lama.pt`

Supported locations:

- `%LOCALAPPDATA%\SlideMaker\models\lama\big-lama.pt` for packaged Windows runs
- `.slide_maker_data/models/lama/big-lama.pt` for source runs
- `SLIDE_MAKER_LAMA_MODEL`
- `LAMA_MODEL`

If LaMa is missing, Slide Maker stops and asks you to configure the model first.

Official upstream model:

- [big-lama.pt](https://github.com/enesmsahin/simple-lama-inpainting/releases/download/v0.1.0/big-lama.pt)

### OCR Models

RapidOCR is used by default. Optional OCR model files can be managed under:

- `.slide_maker_data/models/rapidocr/onnxruntime/`

Helper script:

```bash
python scripts/download_ocr_models.py
```

## Build Notes

### Windows Build

Run on Windows:

```powershell
powershell -ExecutionPolicy Bypass -File .\build.ps1
```

The Windows build uses:

- `Slide_Maker.spec`
- `build.ps1`
- `Slide_Maker_Setup.iss`

The packaged Windows structure is intentionally split:

- `SlideMaker.exe` is the visible PyInstaller desktop shell.
- `portable_python`, `portable_site_packages`, and `portable_app` run the heavier conversion worker.

This is more stable for `torch`, `onnxruntime`, LaMa, and OCR than freezing every worker dependency into one executable.

### Mac Package

The Mac app can be packaged as an `.app` bundle that launches the same desktop entry point from its bundled backend. The Mac package should be attached to the GitHub release before the README advertises it as a public download.

## Verification Summary

- PNG/image conversion was retested with a restricted GUI-like `PATH`.
- PDF conversion was retested with native text extraction, real DPI layout, and high-fidelity Node output.
- `test/Istanbul.pdf` page 1 at 200 DPI generated a correct `13.33 x 7.5 in` PPTX.
- 300 DPI oversized PDF input is now rejected during preflight instead of exhausting memory.
- The Windows portable structure was inspected on macOS, but a full Windows GUI rebuild must be done on Windows.

## Repository Layout

```text
.
|-- ui_app.py
|-- ui/
|-- services/
|-- main.py
|-- extract_pdf.py
|-- image_processor.py
|-- ppt_generator.py
|-- pptx-project/
|-- scripts/
|-- assets/
|-- build.ps1
|-- Slide_Maker.spec
`-- Slide_Maker_Setup.iss
```

## Privacy

Slide Maker is designed to run locally. Files are processed on your machine after dependencies and models are installed or bundled.
