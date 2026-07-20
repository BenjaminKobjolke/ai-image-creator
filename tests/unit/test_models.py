"""Validation rules: size rejection, defaults, output dimension pairing."""

from __future__ import annotations

import pytest
from pathlib import Path
from pydantic import ValidationError

from ai_image_creator import constants
from ai_image_creator.models import CropMode, ImageRequest, OutputSpec


def test_defaults_applied() -> None:
    req = ImageRequest(prompt="a fox")
    assert req.provider == constants.DEFAULT_PROVIDER
    assert req.model == constants.DEFAULT_MODEL
    assert req.size == constants.DEFAULT_SIZE[constants.DEFAULT_MODEL]
    assert req.n == 1


def test_valid_size_accepted() -> None:
    req = ImageRequest(prompt="a fox", model=constants.MODEL_DALL_E_3, size="1792x1024")
    assert req.size == "1792x1024"


def test_invalid_size_rejected() -> None:
    with pytest.raises(ValidationError, match="invalid for model"):
        ImageRequest(prompt="a fox", model=constants.MODEL_GPT_IMAGE_1, size="800x600")


def test_gemini_aspect_ratio_accepted() -> None:
    req = ImageRequest(
        prompt="a fox", model=constants.MODEL_GEMINI_25_FLASH_IMAGE, size="16:9"
    )
    assert req.size == "16:9"


def test_gemini_default_size_is_aspect_ratio() -> None:
    req = ImageRequest(prompt="a fox", model=constants.MODEL_GEMINI_25_FLASH_IMAGE)
    assert req.size == "1:1"


def test_gemini_invalid_size_rejected() -> None:
    with pytest.raises(ValidationError, match="invalid for model"):
        ImageRequest(prompt="a fox", model=constants.MODEL_IMAGEN_4, size="1024x1024")


def test_unknown_model_rejected() -> None:
    with pytest.raises(ValidationError, match="unknown model"):
        ImageRequest(prompt="a fox", model="nope")


def test_output_requires_both_dimensions() -> None:
    with pytest.raises(ValidationError, match="together"):
        OutputSpec(path="out.png", width=800)


def test_output_defaults() -> None:
    spec = OutputSpec(path="out.png")
    assert spec.crop is CropMode.CENTER
    assert spec.has_resize is False


def test_empty_prompt_rejected() -> None:
    with pytest.raises(ValidationError):
        ImageRequest(prompt="")


def test_reference_images_accepted_on_capable_model(tmp_path: Path) -> None:
    ref = tmp_path / "ref.png"
    ref.write_bytes(b"\x89PNG fake")
    req = ImageRequest(prompt="a fox", reference_images=[str(ref)])
    assert req.reference_images == [str(ref)]


def test_reference_images_accepted_on_gemini_flash(tmp_path: Path) -> None:
    ref = tmp_path / "ref.png"
    ref.write_bytes(b"\x89PNG fake")
    req = ImageRequest(
        prompt="a fox",
        provider="gemini",
        model=constants.MODEL_GEMINI_25_FLASH_IMAGE,
        reference_images=[str(ref)],
    )
    assert req.reference_images == [str(ref)]


def test_reference_images_rejected_on_incapable_model(tmp_path: Path) -> None:
    ref = tmp_path / "ref.png"
    ref.write_bytes(b"\x89PNG fake")
    with pytest.raises(ValidationError, match="reference_images"):
        ImageRequest(prompt="a fox", model=constants.MODEL_DALL_E_3, reference_images=[str(ref)])


def test_reference_images_missing_file_rejected() -> None:
    with pytest.raises(ValidationError, match="not found"):
        ImageRequest(prompt="a fox", reference_images=["does/not/exist.png"])


def test_reference_images_empty_list_normalizes_to_none() -> None:
    req = ImageRequest(prompt="a fox", reference_images=[])
    assert req.reference_images is None


def test_background_transparent_accepted() -> None:
    req = ImageRequest(prompt="an icon", background="transparent")
    assert req.background == "transparent"


def test_background_invalid_rejected() -> None:
    with pytest.raises(ValidationError, match="background"):
        ImageRequest(prompt="an icon", background="see-through")
