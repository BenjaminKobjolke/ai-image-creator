"""End-to-end batch through a fake provider — writes real files, no network."""

from __future__ import annotations

import io
from pathlib import Path

from PIL import Image

from ai_image_creator import constants
from ai_image_creator.models import CropMode, ImageRequest, OutputSpec
from ai_image_creator.providers.base import GeneratedImage
from ai_image_creator.runner import run_batch
from ai_image_creator.settings import Settings


class FakeProvider:
    """Returns a solid PNG at the requested provider size for each image."""

    def generate(self, request: ImageRequest) -> list[GeneratedImage]:
        w, h = (int(x) for x in (request.size or "1024x1024").split("x"))
        buf = io.BytesIO()
        Image.new("RGB", (w, h), (200, 100, 50)).save(buf, format="PNG")
        return [
            GeneratedImage(data=buf.getvalue(), source_size=request.size or "")
            for _ in range(request.n)
        ]


def _settings() -> Settings:
    return Settings(
        openai_api_key="sk-test",
        gemini_api_key="gm-test",
        default_provider=constants.DEFAULT_PROVIDER,
        default_model=constants.DEFAULT_MODEL,
        log_level="WARNING",
    )


def _dims(path: str) -> tuple[int, int]:
    with Image.open(path) as img:
        return img.size


def test_batch_writes_files_at_output_size(tmp_path: Path) -> None:
    out_a = tmp_path / "a.png"
    out_b = tmp_path / "b.png"
    requests = [
        ImageRequest(
            prompt="fox",
            size="1024x1024",
            output=OutputSpec(path=str(out_a), width=800, height=600, crop=CropMode.CENTER),
        ),
        ImageRequest(
            prompt="owl",
            model=constants.MODEL_DALL_E_3,
            size="1792x1024",
            output=OutputSpec(path=str(out_b), width=300, height=300, crop=CropMode.STRETCH),
        ),
    ]

    results = run_batch(requests, _settings(), provider_override=FakeProvider())

    assert all(r.ok for r in results)
    assert _dims(str(out_a)) == (800, 600)
    assert _dims(str(out_b)) == (300, 300)


def test_multiple_images_get_distinct_paths(tmp_path: Path) -> None:
    out = tmp_path / "img.png"
    request = ImageRequest(prompt="fox", n=3, output=OutputSpec(path=str(out)))

    results = run_batch([request], _settings(), provider_override=FakeProvider())

    assert len(results) == 3
    assert {r.path for r in results} == {
        str(tmp_path / "img_0.png"),
        str(tmp_path / "img_1.png"),
        str(tmp_path / "img_2.png"),
    }
