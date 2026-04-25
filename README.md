# Slide Maker

[English](README.md) | [Simplified Chinese](README.zh-CN.md)

Slide Maker is a local-first tool that turns PDFs, screenshots, scanned pages, and photographed slides into editable PowerPoint files.

## v0.4.0

- Windows release now ships as a tested portable desktop package
- Background repair now requires LaMa and no longer silently falls back to OpenCV
- Packaged builds prefer the bundled runtime more reliably
- README refreshed for a clearer public release experience

## What It Can Do

- Convert PDF files into editable `.pptx`
- Convert a single image into `.pptx`
- Convert a folder of images into a multi-slide `.pptx`
- Fix perspective for photographed slides before OCR
- Rebuild text boxes from OCR results
- Clean source text from the background with LaMa
- Stay fully local once dependencies and models are ready

## Best Way To Start

### Windows Portable Release

For most users, the easiest path is the packaged Windows release on the [Releases](https://github.com/hamiltonxu650-lang/Slide-Maker/releases) page.

1. Download the latest portable ZIP.
2. Extract it anywhere you want.
3. Put `big-lama.pt` in `%LOCALAPPDATA%\\SlideMaker\\models\\lama\\big-lama.pt`.
4. Launch `SlideMaker.exe`.
5. Convert your PDF or images to `.pptx`.

Notes:

- The packaged Windows build already includes the Node runtime used for the high-fidelity layout pass.
- If you prefer a custom model location, set `SLIDE_MAKER_LAMA_MODEL`.

## Supported Workflows

| Workflow | Windows | macOS | Linux | Notes |
| --- | --- | --- | --- | --- |
| Terminal UI | Yes | Yes | Yes | Good first setup flow |
| CLI | Yes | Yes | Yes | Good for automation |
| Desktop UI from source | Yes | Yes | Yes | Requires PyQt6 |
| Local web app | Yes | Yes | Yes | Runs with FastAPI/Uvicorn |
| Docker web deployment | Yes | Yes | Yes | For self-hosting the local web app |
| Packaged desktop build | Yes | No | No | Current release packaging target |

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
- The main focus right now is local conversion quality and Windows desktop usability.
- The web app is intended for local deployment by default; public hosting is a separate step.
