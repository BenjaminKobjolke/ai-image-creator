"""Map a provider name to a built provider instance.

Adding a provider = add one branch here plus its module. Keeps the CLI/runner
free of provider-construction details.
"""

from __future__ import annotations

from ai_image_creator import constants
from ai_image_creator.providers.base import ImageProvider
from ai_image_creator.settings import Settings


def build_provider(name: str, settings: Settings) -> ImageProvider:
    if name == constants.PROVIDER_OPENAI:
        if not settings.openai_api_key:
            raise ValueError(
                f"{constants.ENV_OPENAI_API_KEY} is not set "
                "(put it in .env, the environment, or pass --api-key)"
            )
        # Imported here so the SDK is only needed when the provider is used.
        from openai import OpenAI

        from ai_image_creator.providers.openai_provider import OpenAIProvider

        return OpenAIProvider(OpenAI(api_key=settings.openai_api_key))

    if name == constants.PROVIDER_GEMINI:
        if not settings.gemini_api_key:
            raise ValueError(
                f"{constants.ENV_GEMINI_API_KEY} is not set "
                "(put it in .env, the environment, or pass --api-key)"
            )
        # Imported here so the SDK is only needed when the provider is used.
        import logging

        from google import genai

        from ai_image_creator.providers.gemini_provider import GeminiProvider

        # We pass the key explicitly, so the SDK's env scan (which warns when both
        # GOOGLE_API_KEY and GEMINI_API_KEY exist) is irrelevant noise here. Mute it.
        logging.getLogger("google_genai._api_client").setLevel(logging.ERROR)
        return GeminiProvider(genai.Client(api_key=settings.gemini_api_key))

    known = ", ".join((constants.PROVIDER_OPENAI, constants.PROVIDER_GEMINI))
    raise ValueError(f"unknown provider {name!r}; known providers: {known}")
