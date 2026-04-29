# Slide Maker

[English](README.md) | [Simplified Chinese](README.zh-CN.md)

Slide Maker is a local-first tool that turns PDFs, screenshots, scanned pages, and photographed slides into editable PowerPoint files.

## v0.4.0

- A Mac desktop version has now been built and used as the visual baseline for the app.
- The Windows desktop frontend has been rebuilt from the Mac frontend so both platforms share the same product UI.
- Windows keeps its own platform shell: Windows title-bar controls, Windows-friendly font fallback, and Windows-only file picker behavior.
- The blurry app icons in the title bar and sidebar were fixed by using the high-resolution PNG asset for in-app display.
- Background repair requires LaMa and no longer silently falls back to OpenCV.
- Packaged builds prefer bundled runtimes more reliably.

## What It Can Do

- Convert PDF files into editable `.pptx`
- Convert a single image into `.pptx`
- Convert a folder of images into a multi-slide `.pptx`
- Fix perspective for photographed slides before OCR
- Rebuild text boxes from OCR results
- Clean source text from the background with LaMa
- Stay fully local once dependencies and models are ready

## Best Way To Start

### Windows Users

Download the Windows build from the [Releases](https://github.com/hamiltonxu650-lang/Slide-Maker/releases) page or use the delivered Windows portable ZIP.

1. Download the latest portable ZIP.
2. Extract it anywhere you want.
3. Launch `SlideMaker.exe`.
4. Convert your PDF or images to `.pptx`.

Notes:

- The packaged Windows build already includes the Node runtime used for the high-fidelity layout pass.
- The packaged Windows build already includes the portable Python runtime, OCR runtime, and LaMa model.
- If you prefer a custom model location, set `SLIDE_MAKER_LAMA_MODEL`.

### Mac Users

Use the Mac version when working on macOS. The Mac desktop frontend is complete, and the Windows frontend is now synced from that same design.

From source, macOS can also run the same desktop entry point:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements.txt
cd pptx-project && npm install && cd ..
python ui_app.py
```

## System Requirements

### Windows Minimum Supported

- Windows 10 or Windows 11, 64-bit
- Intel or AMD x64 CPU
- 16 GB RAM for normal use
- 4 GB free disk space
- No GPU required
- No separate Python or Node.js installation required

### Windows Recommended

- Windows 11, 64-bit
- 16 GB to 32 GB RAM
- SSD storage with 8 GB or more free space
- Modern 4-core CPU or better

### macOS Source Runtime

- macOS with Python 3.9 or newer
- Node.js available on `PATH` for the high-fidelity layout pass
- LaMa model and OCR models configured in `.slide_maker_data/`
- PyQt6 for the desktop UI

### Tested Runtime Notes

The packaged `v0.4.0` Windows release was previously tested as a self-contained portable bundle:

- ZIP download size: about `753 MB`
- Unpacked size: about `1.85 GB`
- Includes `Python 3.10.10`, `Node v24.14.0`, `torch 2.10.0+cpu`, `onnxruntime 1.23.2`, and `big-lama.pt`
- Single-image conversion peaked around `1.5 GB` working set in local tests
- A 3-page PDF conversion peaked around `5.8 GB` working set in local tests

If a user only has `8 GB RAM`, light single-image jobs may still work, but multi-page PDF conversion is not a safe target.

The current Mac-side conversion flow was retested after the frontend sync:

- Image conversion from `test/download.jpg` produced a valid 1-slide `.pptx`.
- PDF conversion from `test/Quiz 1.pdf` produced a valid 3-slide `.pptx`.
- Desktop worker conversion through `ui_app.py --worker` produced a valid `.pptx`.
- The Mac run used RapidOCR, LaMa AI background repair, and Node high-fidelity layout rendering.

The Windows portable package structure was checked on macOS, including `SlideMaker.exe`, bundled Python, bundled Node, OCR models, and `big-lama.pt`. A true Windows output run still needs to be executed on Windows or in a Windows VM because macOS cannot run the Windows executable directly.

## Supported Workflows

| Workflow | Windows | macOS | Linux | Notes |
| --- | --- | --- | --- | --- |
| Terminal UI | Yes | Yes | Yes | Good first setup flow |
| CLI | Yes | Yes | Yes | Good for automation |
| Desktop UI from source | Yes | Yes | Yes | Uses the new shared Mac/Windows frontend |
| Local web app | Yes | Yes | Yes | Runs with FastAPI/Uvicorn |
| Docker web deployment | Yes | Yes | Yes | For self-hosting the local web app |
| Packaged desktop build | Yes | Yes | No | Windows users download Windows; Mac users use the Mac build |

## Quick Start From Source

### Windows

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup_windows.ps1
python terminal_ui.py
```

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements.txt
cd pptx-project && npm install && cd ..
python terminal_ui.py
```

The terminal UI is the easiest source-based entry point because it can inspect the runtime, guide model setup, and run conversions interactively.

## Other Entry Points

### Desktop UI

```bash
python ui_app.py
```

Demo-only preview:

```bash
python ui_app.py --demo
```

The desktop UI is the main user-facing surface after this update. It uses the rebuilt Mac design on both Mac and Windows, while preserving platform-specific window chrome and file support.

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

LaMa is required for background repair in `v0.4.0`.

Expected filename:

- `big-lama.pt`

Supported locations:

- `%LOCALAPPDATA%\\SlideMaker\\models\\lama\\big-lama.pt` for packaged Windows runs
- `.slide_maker_data/models/lama/big-lama.pt` for source runs
- `SLIDE_MAKER_LAMA_MODEL`
- `LAMA_MODEL`

If LaMa is missing, Slide Maker stops and asks you to configure the model first.

Official upstream weight used by the dependency:

- [big-lama.pt](https://github.com/enesmsahin/simple-lama-inpainting/releases/download/v0.1.0/big-lama.pt)

### OCR Models

RapidOCR is supported out of the box, and user-managed OCR models are also supported.

Reserved slot:

- `.slide_maker_data/models/rapidocr/onnxruntime/`

Optional helper:

```bash
python scripts/download_ocr_models.py
```

## Rendering Modes

Slide Maker can finish in two ways:

- High fidelity: uses Node.js and `pptx-project/layout_engine.js` for better layout recovery
- Compatibility: keeps the Python-generated `.pptx` when Node.js is unavailable or compatibility mode is selected

The packaged Windows build automatically prefers the bundled Node runtime.

## Packaging Notes

Windows packaging is driven by:

- `build.ps1`
- `Slide_Maker.spec`
- `Slide_Maker_Setup.iss`

The current packaged app uses a hybrid layout:

- a PyInstaller desktop shell for the visible GUI
- a portable worker runtime under `portable_python`, `portable_site_packages`, and `portable_app`

That design is intentional. It has been more reliable than running a fully frozen worker directly for `torch` and `onnxruntime` heavy jobs.

The Mac build is now part of the project direction as a first-class desktop target. The frontend work done for Mac is the source of the current shared desktop UI, and Windows has been adapted to match it without changing the conversion pipeline.

## Project Layout

```text
.
|-- terminal_ui.py
|-- ui_app.py
|-- run_pipeline.py
|-- web_app.py
|-- services/
|-- ui/
|-- scripts/
|-- web/
|-- pptx-project/
|-- runtime/
|-- assets/
`-- build.ps1
```

## Status

- This repository is an actively developed product workbench, not a polished SDK.
- The main focus right now is local conversion quality and consistent Windows/Mac desktop usability.
- The web app is intended for local deployment by default; public hosting is a separate step.
