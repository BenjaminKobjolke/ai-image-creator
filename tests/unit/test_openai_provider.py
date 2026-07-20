"""OpenAIProvider normalizes b64 and url responses without touching the network."""

from __future__ import annotations

import base64
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from openai import OpenAI

from ai_image_creator.models import ImageRequest
from ai_image_creator.providers.openai_provider import OpenAIProvider


def test_generate_decodes_b64() -> None:
    raw = b"\x89PNG fake bytes"
    item = SimpleNamespace(b64_json=base64.b64encode(raw).decode(), url=None)
    client = MagicMock(spec=OpenAI)
    client.images.generate.return_value = SimpleNamespace(data=[item])

    provider = OpenAIProvider(client)
    images = provider.generate(ImageRequest(prompt="a fox"))

    assert len(images) == 1
    assert images[0].data == raw
    assert images[0].source_size == "1024x1024"


def test_generate_downloads_url() -> None:
    raw = b"downloaded bytes"
    item = SimpleNamespace(b64_json=None, url="https://example.com/i.png")
    client = MagicMock(spec=OpenAI)
    client.images.generate.return_value = SimpleNamespace(data=[item])

    fake_resp = MagicMock()
    fake_resp.read.return_value = raw
    fake_resp.__enter__ = lambda s: fake_resp
    fake_resp.__exit__ = lambda *a: False

    with patch("urllib.request.urlopen", return_value=fake_resp):
        provider = OpenAIProvider(client)
        images = provider.generate(ImageRequest(prompt="a fox", model="dall-e-3"))

    assert images[0].data == raw


def test_quality_forwarded_when_set() -> None:
    item = SimpleNamespace(b64_json=base64.b64encode(b"x").decode(), url=None)
    client = MagicMock(spec=OpenAI)
    client.images.generate.return_value = SimpleNamespace(data=[item])

    OpenAIProvider(client).generate(ImageRequest(prompt="a fox", quality="high"))

    _, kwargs = client.images.generate.call_args
    assert kwargs["quality"] == "high"
