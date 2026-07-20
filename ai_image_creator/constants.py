"""Centralized string constants and provider capability tables.

Kept in one place so raw strings are not scattered across the codebase
(String-Constants rule) and provider size limits have a single source of truth.
"""

from __future__ import annotations

# Provider names
PROVIDER_OPENAI = "openai"
PROVIDER_GEMINI = "gemini"
DEFAULT_PROVIDER = PROVIDER_OPENAI

# OpenAI models (newest first). The first entry is the default model.
MODEL_GPT_IMAGE_2 = "gpt-image-2"
MODEL_GPT_IMAGE_1 = "gpt-image-1"
MODEL_DALL_E_3 = "dall-e-3"
MODEL_DALL_E_2 = "dall-e-2"
DEFAULT_MODEL = MODEL_GPT_IMAGE_2

# Google Gemini models. `gemini-*` use the generate_content API; `imagen-*` use
# generate_images. Imagen models are deprecated by Google (shutdown 2026-08-17).
MODEL_GEMINI_25_FLASH_IMAGE = "gemini-2.5-flash-image"
MODEL_IMAGEN_4 = "imagen-4.0-generate-001"
MODEL_IMAGEN_4_ULTRA = "imagen-4.0-ultra-generate-001"
MODEL_IMAGEN_4_FAST = "imagen-4.0-fast-generate-001"

# Special "let the provider decide" size.
SIZE_AUTO = "auto"

# gpt-image-1 / gpt-image-2 share the same size family.
_GPT_IMAGE_SIZES = ("1024x1024", "1024x1536", "1536x1024", SIZE_AUTO)

# Gemini/Imagen size = an aspect ratio (final pixels come from OutputSpec/Pillow).
_GEMINI_ASPECT_RATIOS = ("1:1", "3:4", "4:3", "9:16", "16:9")

# Valid provider generation sizes per model. `size` in a request is rejected
# at validation time if it is not one of these (fail-fast per design).
VALID_SIZES: dict[str, tuple[str, ...]] = {
    MODEL_GPT_IMAGE_2: _GPT_IMAGE_SIZES,
    MODEL_GPT_IMAGE_1: _GPT_IMAGE_SIZES,
    MODEL_DALL_E_3: ("1024x1024", "1792x1024", "1024x1792"),
    MODEL_DALL_E_2: ("256x256", "512x512", "1024x1024"),
    MODEL_GEMINI_25_FLASH_IMAGE: _GEMINI_ASPECT_RATIOS,
    MODEL_IMAGEN_4: _GEMINI_ASPECT_RATIOS,
    MODEL_IMAGEN_4_ULTRA: _GEMINI_ASPECT_RATIOS,
    MODEL_IMAGEN_4_FAST: _GEMINI_ASPECT_RATIOS,
}

# Default generation size per model (used when a request omits `size`).
DEFAULT_SIZE: dict[str, str] = {
    MODEL_GPT_IMAGE_2: "1024x1024",
    MODEL_GPT_IMAGE_1: "1024x1024",
    MODEL_DALL_E_3: "1024x1024",
    MODEL_DALL_E_2: "1024x1024",
    MODEL_GEMINI_25_FLASH_IMAGE: "1:1",
    MODEL_IMAGEN_4: "1:1",
    MODEL_IMAGEN_4_ULTRA: "1:1",
    MODEL_IMAGEN_4_FAST: "1:1",
}

# Output file defaults.
DEFAULT_OUTPUT_DIR = "output"
DEFAULT_OUTPUT_FORMAT = "png"

# Environment variable names.
ENV_OPENAI_API_KEY = "OPENAI_API_KEY"
ENV_GEMINI_API_KEY = "GEMINI_API_KEY"
ENV_LOG_LEVEL = "AI_IMAGE_CREATOR_LOG_LEVEL"

# Logger name.
LOGGER_NAME = "ai_image_creator"
