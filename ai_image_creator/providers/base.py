"""Provider contract. New providers implement `ImageProvider`.

The one method returns typed `GeneratedImage` objects (raw bytes), never a
dict, so shape bugs surface (No-Bag-of-Keys rule).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from ai_image_creator.models import ImageRequest


@dataclass(frozen=True)
class GeneratedImage:
    data: bytes  # raw image bytes as returned/decoded from the provider
    source_size: str  # the provider size used to generate it, e.g. "1024x1024"


class ImageProvider(Protocol):
    def generate(self, request: ImageRequest) -> list[GeneratedImage]:
        """Generate `request.n` images. Returns raw bytes per image."""
        ...
