import argparse

from services.app_models import APP_BRAND
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
    args = parser.parse_args()

    run_conversion(
        args.input,
        output_path=args.output,
        auto_open=not args.no_open,
    )


if __name__ == "__main__":
    main()
