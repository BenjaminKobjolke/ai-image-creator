"""Output post-processing: exact dimensions for crop + stretch."""

from __future__ import annotations

import io

from PIL import Image

from ai_image_creator.models import CropMode, OutputSpec
from ai_image_creator.processing.image_output import resize_and_crop


def _png_bytes(width: int, height: int) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (width, height), (10, 20, 30)).save(buf, format="PNG")
    return buf.getvalue()


def _dimensions(data: bytes) -> tuple[int, int]:
    with Image.open(io.BytesIO(data)) as img:
        return img.size


def test_center_crop_produces_exact_size() -> None:
    src = _png_bytes(1024, 1024)
    spec = OutputSpec(path="out.png", width=800, height=600, crop=CropMode.CENTER)
    assert _dimensions(resize_and_crop(src, spec)) == (800, 600)


def test_stretch_produces_exact_size() -> None:
    src = _png_bytes(1024, 1024)
    spec = OutputSpec(path="out.png", width=300, height=900, crop=CropMode.STRETCH)
    assert _dimensions(resize_and_crop(src, spec)) == (300, 900)


def test_anchor_modes_all_hit_target() -> None:
    src = _png_bytes(1000, 500)
    for mode in (CropMode.TOP, CropMode.BOTTOM, CropMode.LEFT, CropMode.RIGHT):
        spec = OutputSpec(path="out.png", width=400, height=400, crop=mode)
        assert _dimensions(resize_and_crop(src, spec)) == (400, 400)


def test_no_resize_reencodes() -> None:
    src = _png_bytes(512, 512)
    spec = OutputSpec(path="out.png")  # no width/height -> re-encode as-is
    assert _dimensions(resize_and_crop(src, spec)) == (512, 512)
