"""GeminiProvider normalizes both API shapes into raw bytes without the network."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from google import genai

from ai_image_creator.models import ImageRequest
from ai_image_creator.providers.gemini_provider import GeminiProvider


def _content_response(raw: bytes) -> SimpleNamespace:
    part = SimpleNamespace(inline_data=SimpleNamespace(data=raw))
    content = SimpleNamespace(parts=[part])
    return SimpleNamespace(candidates=[SimpleNamespace(content=content)])


def test_gemini_flash_extracts_inline_bytes() -> None:
    raw = b"\x89PNG gemini bytes"
    client = MagicMock(spec=genai.Client)
    client.models.generate_content.return_value = _content_response(raw)

    provider = GeminiProvider(client)
    images = provider.generate(
        ImageRequest(prompt="a fox", provider="gemini", model="gemini-2.5-flash-image")
    )

    assert len(images) == 1
    assert images[0].data == raw
    assert images[0].source_size == "1:1"


def test_gemini_flash_loops_n_calls() -> None:
    client = MagicMock(spec=genai.Client)
    client.models.generate_content.return_value = _content_response(b"x")

    GeminiProvider(client).generate(
        ImageRequest(prompt="a fox", provider="gemini", model="gemini-2.5-flash-image", n=3)
    )

    assert client.models.generate_content.call_count == 3


def test_imagen_extracts_image_bytes() -> None:
    raw = b"imagen bytes"
    item = SimpleNamespace(image=SimpleNamespace(image_bytes=raw))
    client = MagicMock(spec=genai.Client)
    client.models.generate_images.return_value = SimpleNamespace(generated_images=[item])

    images = GeminiProvider(client).generate(
        ImageRequest(prompt="a fox", provider="gemini", model="imagen-4.0-generate-001", size="16:9")
    )

    assert images[0].data == raw
    assert images[0].source_size == "16:9"


def test_no_image_data_raises() -> None:
    client = MagicMock(spec=genai.Client)
    client.models.generate_content.return_value = SimpleNamespace(candidates=[])

    with pytest.raises(ValueError, match="no inline image data"):
        GeminiProvider(client).generate(
            ImageRequest(prompt="a fox", provider="gemini", model="gemini-2.5-flash-image")
        )
