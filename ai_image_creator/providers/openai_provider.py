"""OpenAI image provider.

Normalizes the two response shapes OpenAI returns into raw bytes:
  * `gpt-image-1` -> `b64_json` (decode)
  * dall-e models -> image `url` (download)
"""

from __future__ import annotations

import base64
import urllib.request
from typing import Any

from openai import OpenAI

from ai_image_creator.models import ImageRequest
from ai_image_creator.providers.base import GeneratedImage


class OpenAIProvider:
    def __init__(self, client: OpenAI) -> None:
        # Injected so tests can pass a mock (Inject-Collaborators rule).
        self._client = client

    def generate(self, request: ImageRequest) -> list[GeneratedImage]:
        assert request.size is not None  # resolved by ImageRequest validator
        kwargs: dict[str, Any] = {
            "model": request.model,
            "prompt": request.prompt,
            "size": request.size,
            "n": request.n,
        }
        if request.quality is not None:
            kwargs["quality"] = request.quality

        response = self._client.images.generate(**kwargs)
        if response.data is None:
            return []
        return [
            GeneratedImage(data=self._extract_bytes(item), source_size=request.size)
            for item in response.data
        ]

    @staticmethod
    def _extract_bytes(item: object) -> bytes:
        b64 = getattr(item, "b64_json", None)
        if b64:
            return base64.b64decode(b64)
        url = getattr(item, "url", None)
        if url:
            with urllib.request.urlopen(url) as resp:  # noqa: S310 - trusted OpenAI URL
                return bytes(resp.read())
        raise ValueError("OpenAI image item had neither b64_json nor url")
