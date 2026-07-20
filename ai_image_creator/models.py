"""Typed request/output models validated at the JSON boundary (Pydantic).

Two size concepts are kept deliberately separate:
  * `ImageRequest.size` — what the provider generates; rejected if it is not a
    valid size for the chosen model.
  * `OutputSpec` — the desired final file (any width/height + crop), produced by
    post-processing the generated image with Pillow.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ai_image_creator import constants


class CropMode(str, Enum):
    CENTER = "center"
    TOP = "top"
    BOTTOM = "bottom"
    LEFT = "left"
    RIGHT = "right"
    STRETCH = "stretch"


class OutputSpec(BaseModel):
    """Desired final image on disk. Optional per request."""

    model_config = ConfigDict(extra="forbid")

    path: str
    width: int | None = Field(default=None, gt=0)
    height: int | None = Field(default=None, gt=0)
    crop: CropMode = CropMode.CENTER
    format: str = constants.DEFAULT_OUTPUT_FORMAT

    @model_validator(mode="after")
    def _both_or_neither_dimension(self) -> "OutputSpec":
        if (self.width is None) != (self.height is None):
            raise ValueError("output.width and output.height must be set together")
        return self

    @property
    def has_resize(self) -> bool:
        return self.width is not None and self.height is not None


class ImageRequest(BaseModel):
    """One image generation request (one element of the batch JSON list)."""

    model_config = ConfigDict(extra="forbid")

    prompt: str = Field(min_length=1)
    provider: str = constants.DEFAULT_PROVIDER
    model: str = constants.DEFAULT_MODEL
    size: str | None = None
    n: int = Field(default=1, ge=1)
    quality: str | None = None
    output: OutputSpec | None = None

    @model_validator(mode="after")
    def _resolve_and_validate_size(self) -> "ImageRequest":
        valid = constants.VALID_SIZES.get(self.model)
        if valid is None:
            raise ValueError(
                f"unknown model {self.model!r}; valid models: {', '.join(constants.VALID_SIZES)}"
            )
        if self.size is None:
            object.__setattr__(self, "size", constants.DEFAULT_SIZE[self.model])
        elif self.size not in valid:
            raise ValueError(
                f"size {self.size!r} is invalid for model {self.model!r}; "
                f"valid sizes: {', '.join(valid)}"
            )
        return self
