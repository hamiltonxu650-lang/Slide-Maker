from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _first_existing(*paths):
    for path in paths:
        if path.exists():
            return path
    return None


# Temporary local defaults until the user sends final hero artwork.
PDF_HERO_IMAGE = _first_existing(
    PROJECT_ROOT / "test" / "Slide1.JPG",
    PROJECT_ROOT / "test" / "extracted_quiz1" / "page_001.png",
)

IMAGE_HERO_IMAGE = _first_existing(
    PROJECT_ROOT / "test" / "Slide2.JPG",
    PROJECT_ROOT / "test" / "未命名的设计.png",
)
