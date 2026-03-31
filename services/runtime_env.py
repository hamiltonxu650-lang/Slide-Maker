from __future__ import annotations

import os
from pathlib import Path
import shutil
import sys
import ctypes

from services.app_models import app_data_root, describe_lama_model_setup, describe_ocr_model_setup


_DLL_DIRECTORY_HANDLES = []


def get_runtime_roots() -> list[Path]:
    roots = []
    executable_root = Path(sys.executable).resolve().parent
    roots.append(executable_root)

    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        roots.append(Path(meipass))

    roots.append(Path(__file__).resolve().parents[1])

    unique = []
    seen = set()
    for root in roots:
        key = str(root).lower()
        if key not in seen:
            unique.append(root)
            seen.add(key)
    return unique


def _unique_existing_paths(paths: list[Path]) -> list[Path]:
    unique = []
    seen = set()
    for path in paths:
        try:
            resolved = path.resolve()
        except OSError:
            resolved = path
        key = str(resolved).lower()
        if key in seen or not resolved.exists():
            continue
        seen.add(key)
        unique.append(resolved)
    return unique


def get_runtime_binary_dirs() -> list[Path]:
    candidates = []
    for root in get_runtime_roots():
        candidates.extend(
            [
                root,
                root / "_internal",
                root / "onnxruntime" / "capi",
                root / "_internal" / "onnxruntime" / "capi",
                root / "torch" / "lib",
                root / "_internal" / "torch" / "lib",
                root / "pymupdf",
                root / "_internal" / "pymupdf",
            ]
        )
    return _unique_existing_paths(candidates)


def configure_runtime_dll_search_paths() -> list[str]:
    if os.name != "nt":
        return []

    added = []
    path_entries = os.environ.get("PATH", "").split(os.pathsep)
    normalized_path = {entry.lower() for entry in path_entries if entry}

    for directory in get_runtime_binary_dirs():
        directory_text = str(directory)
        if directory_text.lower() not in normalized_path:
            os.environ["PATH"] = directory_text + os.pathsep + os.environ.get("PATH", "")
            normalized_path.add(directory_text.lower())

        if hasattr(os, "add_dll_directory"):
            try:
                handle = os.add_dll_directory(directory_text)
            except OSError:
                handle = None
            if handle is not None:
                _DLL_DIRECTORY_HANDLES.append(handle)

        added.append(directory_text)
    return added


def preload_runtime_libraries() -> dict[str, list[str]]:
    if os.name != "nt":
        return {"loaded": [], "failed": []}

    loaded: list[str] = []
    failed: list[str] = []

    preferred = [
        ("", "vcruntime140.dll"),
        ("", "vcruntime140_1.dll"),
        ("torch/lib", "libiomp5md.dll"),
        ("torch/lib", "shm.dll"),
        ("torch/lib", "c10.dll"),
        ("torch/lib", "torch_cpu.dll"),
        ("torch/lib", "torch_python.dll"),
        ("onnxruntime/capi", "onnxruntime.dll"),
        ("onnxruntime/capi", "onnxruntime_providers_shared.dll"),
    ]

    seen = set()
    ordered_candidates: list[Path] = []
    for root in get_runtime_roots():
        for prefix, filename in preferred:
            candidate = root.joinpath(prefix, filename) if prefix else root / filename
            key = str(candidate).lower()
            if key not in seen and candidate.exists():
                seen.add(key)
                ordered_candidates.append(candidate)

    for root in get_runtime_roots():
        for pattern in ("torch/lib/*.dll", "onnxruntime/capi/*.dll"):
            for candidate in sorted(root.glob(pattern)):
                key = str(candidate).lower()
                if key not in seen and candidate.exists():
                    seen.add(key)
                    ordered_candidates.append(candidate)

    for candidate in ordered_candidates:
        try:
            ctypes.WinDLL(str(candidate))
            loaded.append(str(candidate))
        except OSError as exc:
            failed.append(f"{candidate}: {exc}")
    return {"loaded": loaded, "failed": failed}


def detect_project_root() -> Path:
    for root in get_runtime_roots():
        if (root / "pptx-project").exists():
            return root
    return get_runtime_roots()[0]


def resolve_asset_path(*parts: str) -> Path:
    for root in get_runtime_roots():
        candidate = root.joinpath(*parts)
        if candidate.exists():
            return candidate
    return get_runtime_roots()[0].joinpath(*parts)


def find_app_icon() -> Path | None:
    return _first_existing_asset("assets", "slide_maker_icon.ico") or _first_existing_asset(
        "assets", "slide_maker_icon.png"
    )


def _first_existing_asset(*parts: str) -> Path | None:
    for root in get_runtime_roots():
        candidate = root.joinpath(*parts)
        if candidate.exists():
            return candidate
    return None


def _is_runnable_node_candidate(candidate: Path) -> bool:
    if not candidate or not candidate.exists() or candidate.is_dir():
        return False

    name = candidate.name.lower()
    if os.name == "nt":
        return name in {"node.exe", "node"}

    if name.endswith(".exe"):
        return False

    return os.access(candidate, os.X_OK)


def find_node_executable(project_root: Path | None = None):
    project_root = project_root or detect_project_root()
    candidates = []

    node_on_path = shutil.which("node")
    if node_on_path:
        candidates.append(Path(node_on_path))

    for root in get_runtime_roots():
        if os.name == "nt":
            candidates.extend(
                [
                    root / "runtime" / "node.exe",
                    root / "runtime" / "node",
                    root / "_internal" / "runtime" / "node.exe",
                    root / "_internal" / "runtime" / "node",
                    root / "node.exe",
                    root / "node",
                    root / "nodejs" / "node.exe",
                    root / "nodejs" / "node",
                ]
            )
        else:
            candidates.extend(
                [
                    root / "runtime" / "node",
                    root / "_internal" / "runtime" / "node",
                    root / "node",
                    root / "nodejs" / "node",
                ]
            )

    candidates.extend(
        [
            project_root / "runtime" / "node",
            Path("/opt/homebrew/bin/node"),
            Path("/usr/local/bin/node"),
            Path("/usr/bin/node"),
        ]
    )

    if os.name == "nt":
        candidates.extend(
            [
                project_root / "runtime" / "node.exe",
                Path(r"C:\Program Files\nodejs\node.exe"),
                Path(r"C:\Program Files (x86)\nodejs\node.exe"),
                Path(os.path.expandvars(r"%APPDATA%\nodejs\node.exe")),
                Path(os.path.expandvars(r"%LOCALAPPDATA%\bin\node.exe")),
            ]
        )

    for candidate in candidates:
        if _is_runnable_node_candidate(candidate):
            return str(candidate)
    return None


def describe_runtime_environment(project_root: Path | None = None) -> dict:
    project_root = project_root or detect_project_root()
    node_path = find_node_executable(project_root)
    lama_info = describe_lama_model_setup(project_root)
    ocr_info = describe_ocr_model_setup(project_root)
    return {
        "high_fidelity_available": bool(node_path),
        "node_path": node_path,
        "project_root": str(project_root),
        "log_dir": str(app_data_root(project_root) / "logs"),
        "lama_model_available": bool(lama_info["available"]),
        "lama_model_path": str(lama_info["model_path"]),
        "lama_model_slot": str(lama_info["slot_path"]),
        "lama_model_source": str(lama_info["source"]),
        "lama_model_message": str(lama_info["message"]),
        "ocr_model_slot_dir": str(ocr_info["slot_dir"]),
        "ocr_model_custom_count": int(ocr_info["custom_model_count"]),
        "ocr_model_custom_complete": bool(ocr_info["custom_model_complete"]),
        "ocr_model_has_invalid": bool(ocr_info["has_invalid_custom_model"]),
        "ocr_model_message": str(ocr_info["message"]),
    }
