"""Centralized, environment-driven settings.

Everything reads from `Settings`, never from `os.getenv` scattered around
(No-Hardcoded-Env-Values / Centralized-Config rules). Values come from the
environment, optionally loaded from a `.env` file via python-dotenv.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

from ai_image_creator import constants


@dataclass(frozen=True)
class Settings:
    openai_api_key: str | None
    gemini_api_key: str | None
    default_provider: str
    default_model: str
    log_level: str

    @classmethod
    def load(cls, *, api_key_override: str | None = None) -> "Settings":
        """Build settings from the environment (loading `.env` if present).

        `api_key_override` (e.g. a CLI `--api-key`) wins over the environment and
        is applied to every provider key, so one flag works for whichever provider
        the request selects.
        """
        load_dotenv()
        return cls(
            openai_api_key=api_key_override or os.getenv(constants.ENV_OPENAI_API_KEY),
            gemini_api_key=api_key_override or os.getenv(constants.ENV_GEMINI_API_KEY),
            default_provider=constants.DEFAULT_PROVIDER,
            default_model=constants.DEFAULT_MODEL,
            log_level=os.getenv(constants.ENV_LOG_LEVEL, "INFO"),
        )
