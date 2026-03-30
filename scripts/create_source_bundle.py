from __future__ import annotations

from pathlib import Path
import sys
import zipfile


INCLUDE_FILES = {
    ".gitignore",
    "MAC_WINDOWS_TRANSFER_GUIDE.md",
    "Slide_Maker_Master_Development_Record.md",
    "Project_Development_Log.md",
    "PROJECT_SUMMARY.md",
    "Slide_Maker_Conversation_Full_Log.md",
    "requirements.txt",
    "build.ps1",
    "ui_app.py",
    "gui_conversion_runner.py",
    "main.py",
    "extract_pdf.py",
    "image_processor.py",
    "inpainting_engine.py",
    "ocr_engine.py",
    "winrt_ocr_engine.py",
    "ppt_generator.py",
    "utils.py",
    "open_ppt_helper.py",
    "notebook_ppt_converter_architecture.md",
}

INCLUDE_DIRS = {
    "services",
    "ui",
    "assets",
    "models",
    "runtime",
    "pptx-project",
    "scripts",
    "test",
}

EXCLUDE_DIR_NAMES = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".slide_maker_data",
    "build",
    "dist",
    "portable_python",
    "portable_site_packages",
    "portable_app",
    "node_modules",
}

EXCLUDE_SUFFIXES = {
    ".pyc",
    ".pyo",
    ".pyd",
    ".obj",
    ".lib",
    ".exp",
}

EXCLUDE_FILE_NAMES = {
    "Thumbs.db",
    ".DS_Store",
}


def should_skip(path: Path, root: Path) -> bool:
    rel = path.relative_to(root)
    if any(part in EXCLUDE_DIR_NAMES for part in rel.parts):
        return True
    if path.name in EXCLUDE_FILE_NAMES:
        return True
    if path.suffix.lower() in EXCLUDE_SUFFIXES:
        return True
    return False


def iter_paths(root: Path):
    for name in sorted(INCLUDE_FILES):
        path = root / name
        if path.exists() and path.is_file():
            yield path

    for directory in sorted(INCLUDE_DIRS):
        base = root / directory
        if not base.exists():
            continue
        for path in sorted(base.rglob("*")):
            if path.is_dir() or should_skip(path, root):
                continue
            yield path


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    output = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path.home() / "Desktop" / "Slide_Maker_Source.zip"
    output.parent.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for path in iter_paths(root):
            archive.write(path, path.relative_to(root))

    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
