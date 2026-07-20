"""CLI entry point.

Two input modes, one pipeline:
  * positional JSON file -> a list of requests (batch)
  * --prompt (+ options) -> a single-request batch
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from pydantic import ValidationError

from ai_image_creator import constants
from ai_image_creator.app_logger import AppLogger
from ai_image_creator.models import CropMode, ImageRequest, OutputSpec
from ai_image_creator.runner import run_batch
from ai_image_creator.settings import Settings


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    settings = Settings.load(api_key_override=args.api_key)
    AppLogger.configure(settings.log_level)
    log = AppLogger.get()

    try:
        requests = _build_requests(args)
    except (ValidationError, ValueError, json.JSONDecodeError) as exc:
        log.error("invalid input: %s", exc)
        return 2

    if not requests:
        log.error("no requests to process")
        return 2

    results = run_batch(requests, settings)
    ok = sum(1 for r in results if r.ok)
    failed = len(results) - ok
    log.info("done: %d saved, %d failed", ok, failed)
    return 0 if failed == 0 else 1


def _build_requests(args: argparse.Namespace) -> list[ImageRequest]:
    if args.json_path:
        raw = json.loads(Path(args.json_path).read_text(encoding="utf-8"))
        if not isinstance(raw, list):
            raise ValueError("JSON root must be a list of request objects")
        return [ImageRequest.model_validate(item) for item in raw]

    output = None
    if args.output:
        output = OutputSpec(
            path=args.output,
            width=args.width,
            height=args.height,
            crop=CropMode(args.crop),
            format=args.format,
        )
    request = ImageRequest(
        prompt=args.prompt,
        provider=args.provider,
        model=args.model,
        size=args.size,
        n=args.n,
        quality=args.quality,
        output=output,
    )
    return [request]


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="ai-image-creator",
        description="Create images with AI from a JSON batch file or CLI arguments.",
    )
    parser.add_argument(
        "json_path",
        nargs="?",
        help="Path to a JSON file containing a list of image requests (batch mode).",
    )
    parser.add_argument("--prompt", help="Prompt for a single image (single-request mode).")
    parser.add_argument("--provider", default=constants.DEFAULT_PROVIDER)
    parser.add_argument("--model", default=constants.DEFAULT_MODEL)
    parser.add_argument("--size", default=None, help="Provider size, e.g. 1024x1024.")
    parser.add_argument("--n", type=int, default=1, help="Number of images to generate.")
    parser.add_argument("--quality", default=None)
    parser.add_argument(
        "--api-key", default=None, help="Overrides OPENAI_API_KEY and GEMINI_API_KEY."
    )
    # Output post-processing.
    parser.add_argument("--output", default=None, help="Output file path.")
    parser.add_argument("--width", type=int, default=None, help="Final width (with --height).")
    parser.add_argument("--height", type=int, default=None, help="Final height (with --width).")
    parser.add_argument(
        "--crop",
        default=CropMode.CENTER.value,
        choices=[c.value for c in CropMode],
        help="Crop mode when resizing output.",
    )
    parser.add_argument("--format", default=constants.DEFAULT_OUTPUT_FORMAT)

    args = parser.parse_args(argv)
    if bool(args.json_path) == bool(args.prompt):
        parser.error("provide exactly one of: a JSON file path OR --prompt")
    return args


if __name__ == "__main__":
    sys.exit(main())
