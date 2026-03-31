#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import shutil
import sys
import urllib.request


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from services.app_models import OCR_MODEL_DOWNLOADS, ocr_model_slot_dir  # noqa: E402


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download_file(url: str, destination: Path) -> None:
    tmp_path = destination.with_suffix(destination.suffix + ".part")
    tmp_path.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url) as response, tmp_path.open("wb") as handle:
        shutil.copyfileobj(response, handle)
    tmp_path.replace(destination)


def main() -> int:
    parser = argparse.ArgumentParser(description="Download the 3 RapidOCR ONNX models into the reserved slot.")
    parser.add_argument(
        "--output-dir",
        default=str(ocr_model_slot_dir(ROOT_DIR)),
        help="Directory where the OCR model files should be stored.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Redownload files even if they already exist and pass checksum validation.",
    )
    args = parser.parse_args()

    output_dir = Path(args.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    for model_kind, info in OCR_MODEL_DOWNLOADS.items():
        destination = output_dir / info["filename"]
        expected_sha256 = str(info["sha256"]).lower()
        url = str(info["url"])

        if destination.exists() and not args.force:
            actual_sha256 = sha256_file(destination)
            if actual_sha256 == expected_sha256:
                print(f"[skip] {model_kind}: {destination}")
                continue
            print(f"[warn] {model_kind}: checksum mismatch, redownloading {destination}")

        print(f"[download] {model_kind}: {url}")
        download_file(url, destination)
        actual_sha256 = sha256_file(destination)
        if actual_sha256 != expected_sha256:
            raise SystemExit(
                f"Checksum mismatch for {destination}. expected={expected_sha256} actual={actual_sha256}"
            )
        print(f"[ok] {model_kind}: {destination}")

    print(f"\nOCR models are ready in: {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
