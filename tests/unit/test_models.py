"""Validation rules: size rejection, defaults, output dimension pairing."""

from __future__ import annotations

import pytest
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
