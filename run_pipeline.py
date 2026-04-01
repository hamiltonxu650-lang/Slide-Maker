import argparse

from services.app_models import APP_BRAND, AppSettings
from services.conversion_service import run_conversion


def main():
    parser = argparse.ArgumentParser(description=f"{APP_BRAND} command-line conversion entrypoint")
    parser.add_argument("input", help="Input PDF, image file, or directory of images")
    parser.add_argument("--output", default="Result_Presentation.pptx", help="Output .pptx filename")
    parser.add_argument(
        "--no-open",
        action="store_true",
        help="Do not prompt to open the generated PPTX after conversion.",
    )
    parser.add_argument(
        "--scan",
        action="store_true",
        help="Enable document scanner for skewed photos of slides",
    )
    args = parser.parse_args()

    settings = AppSettings(enable_document_scanner=args.scan)

    run_conversion(
        args.input,
        output_path=args.output,
        auto_open=not args.no_open,
        settings=settings,
    )


if __name__ == "__main__":
    main()
