"""Batch orchestration: request -> provider -> post-process -> save.

Sequential on purpose.
# ponytail: sequential batch; swap to AsyncOpenAI + asyncio.gather if batch
# latency ever matters. O(n) API calls, one at a time — fine for CLI use.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ai_image_creator import constants
from ai_image_creator.app_logger import AppLogger
from ai_image_creator.models import ImageRequest
from ai_image_creator.processing import image_output
from ai_image_creator.providers.base import ImageProvider
from ai_image_creator.providers.registry import build_provider
from ai_image_creator.settings import Settings

_log = AppLogger.get()


@dataclass(frozen=True)
class RequestResult:
    path: str
    ok: bool
    error: str | None = None


def run_batch(
    requests: list[ImageRequest],
    settings: Settings,
    *,
    provider_override: ImageProvider | None = None,
) -> list[RequestResult]:
    """Process every request. One request's failure does not abort the batch."""
    results: list[RequestResult] = []
    providers: dict[str, ImageProvider] = {}

    for req_index, request in enumerate(requests):
        try:
            provider = provider_override or _get_provider(request.provider, settings, providers)
            images = provider.generate(request)
            _log.info("generated %d image(s) for request %d", len(images), req_index)
            for img_index, image in enumerate(images):
                path = _resolve_path(request, req_index, img_index, len(images))
                if request.output is not None:
                    # resize_and_crop re-encodes to the requested format even with no resize.
                    data = image_output.resize_and_crop(image.data, request.output)
                else:
                    data = image.data
                saved = image_output.save(data, path)
                _log.info("saved %s", saved)
                results.append(RequestResult(path=str(saved), ok=True))
        except Exception as exc:  # noqa: BLE001 - centralized per-request error boundary
            _log.error("request %d failed: %s", req_index, exc)
            results.append(RequestResult(path="", ok=False, error=str(exc)))

    return results


def _get_provider(name: str, settings: Settings, cache: dict[str, ImageProvider]) -> ImageProvider:
    if name not in cache:
        cache[name] = build_provider(name, settings)
    return cache[name]


def _resolve_path(request: ImageRequest, req_index: int, img_index: int, total: int) -> str:
    if request.output is not None:
        base = Path(request.output.path)
        if total > 1:
            base = base.with_name(f"{base.stem}_{img_index}{base.suffix}")
        return str(base)
    fmt = constants.DEFAULT_OUTPUT_FORMAT
    return str(Path(constants.DEFAULT_OUTPUT_DIR) / f"{req_index}_{img_index}.{fmt}")
