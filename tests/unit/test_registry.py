"""Registry: known name builds a provider, unknown/missing-key fail clearly."""

from __future__ import annotations

import pytest

from ai_image_creator import constants
from ai_image_creator.providers.openai_provider import OpenAIProvider
from ai_image_creator.providers.registry import build_provider
from ai_image_creator.settings import Settings


def _settings(api_key: str | None) -> Settings:
    return Settings(
        openai_api_key=api_key,
        gemini_api_key=api_key,
        default_provider=constants.DEFAULT_PROVIDER,
        default_model=constants.DEFAULT_MODEL,
        log_level="INFO",
    )


def test_openai_provider_built() -> None:
    provider = build_provider(constants.PROVIDER_OPENAI, _settings("sk-test"))
    assert isinstance(provider, OpenAIProvider)


def test_gemini_provider_built() -> None:
    from ai_image_creator.providers.gemini_provider import GeminiProvider

    provider = build_provider(constants.PROVIDER_GEMINI, _settings("gm-test"))
    assert isinstance(provider, GeminiProvider)


def test_missing_key_raises() -> None:
    with pytest.raises(ValueError, match=constants.ENV_OPENAI_API_KEY):
        build_provider(constants.PROVIDER_OPENAI, _settings(None))


def test_missing_gemini_key_raises() -> None:
    with pytest.raises(ValueError, match=constants.ENV_GEMINI_API_KEY):
        build_provider(constants.PROVIDER_GEMINI, _settings(None))


def test_unknown_provider_raises() -> None:
    with pytest.raises(ValueError, match="unknown provider"):
        build_provider("midjourney", _settings("sk-test"))
