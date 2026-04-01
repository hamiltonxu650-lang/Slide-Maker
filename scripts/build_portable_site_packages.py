from __future__ import annotations

from importlib import metadata
from pathlib import Path
from packaging.requirements import Requirement
from packaging.utils import canonicalize_name
import shutil
import sys


ROOT_DISTRIBUTIONS = [
    "simple-lama-inpainting",
    "python-pptx",
    "Pillow",
    "opencv-python",
    "numpy",
    "rapidocr-onnxruntime",
    "onnxruntime",
    "wordninja",
    "PyMuPDF",
    "winrt-Windows.Media.Ocr",
    "winrt-Windows.Graphics.Imaging",
    "winrt-Windows.Foundation",
    "winrt-Windows.Foundation.Collections",
    "winrt-Windows.Storage",
    "winrt-Windows.Storage.Streams",
]

SKIP_DIR_NAMES = {"__pycache__", "test", "tests"}
SKIP_SUFFIXES = {".pyc", ".pyo"}


def build_distribution_index(site_packages_root: Path) -> dict[str, metadata.Distribution]:
    distributions: dict[str, metadata.Distribution] = {}
    for dist in metadata.distributions(path=[str(site_packages_root)]):
        name = canonicalize_name(str(dist.metadata.get("Name") or "").strip())
        if name:
            distributions[name] = dist
    return distributions


def resolve_dependency_closure(index: dict[str, metadata.Distribution]) -> list[metadata.Distribution]:
    selected: set[str] = set()
    queue = [canonicalize_name(name) for name in ROOT_DISTRIBUTIONS]
    missing: set[str] = set()

    while queue:
        name = queue.pop()
        if name in selected:
            continue

        dist = index.get(name)
        if dist is None:
            missing.add(name)
            continue

        selected.add(name)
        for requirement_text in dist.requires or []:
            requirement = Requirement(requirement_text)
            if requirement.marker is not None and not requirement.marker.evaluate():
                continue
            queue.append(canonicalize_name(requirement.name))

    if missing:
        missing_text = ", ".join(sorted(missing))
        raise SystemExit(f"Missing required distributions in site-packages: {missing_text}")

    return [index[name] for name in sorted(selected)]


def should_skip(relative_path: Path) -> bool:
    if any(part in SKIP_DIR_NAMES for part in relative_path.parts):
        return True
    if relative_path.suffix.lower() in SKIP_SUFFIXES:
        return True
    return False


def copy_distribution_files(
    dist: metadata.Distribution,
    source_root: Path,
    destination_root: Path,
) -> None:
    for file_entry in dist.files or ():
        relative_path = Path(file_entry)
        if should_skip(relative_path):
            continue

        source_path = Path(dist.locate_file(file_entry))
        if not source_path.exists() or source_path.is_dir():
            continue

        try:
            source_path.relative_to(source_root)
        except ValueError:
            continue

        target_path = destination_root / relative_path
        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, target_path)


def main() -> int:
    if len(sys.argv) != 3:
        raise SystemExit("Usage: build_portable_site_packages.py <source_site_packages> <destination>")

    source_root = Path(sys.argv[1]).resolve()
    destination_root = Path(sys.argv[2]).resolve()
    if not source_root.exists():
        raise SystemExit(f"Source site-packages not found: {source_root}")

    shutil.rmtree(destination_root, ignore_errors=True)
    destination_root.mkdir(parents=True, exist_ok=True)

    distribution_index = build_distribution_index(source_root)
    selected = resolve_dependency_closure(distribution_index)
    for dist in selected:
        copy_distribution_files(dist, source_root, destination_root)

    print("\n".join(dist.metadata["Name"] for dist in selected))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
