"""Google Gemini image provider.

Two Gemini API shapes, routed by model id:
  * `imagen-*`  -> `client.models.generate_images` (native `n`, image bytes on
    `generated_images[i].image.image_bytes`)
  * `gemini-*`  -> `client.models.generate_content` (one image per call, bytes on
    an inline-data part; looped `request.n` times)

Gemini `size` is an aspect ratio (e.g. "16:9"); final on-disk pixels are the
provider-independent Pillow step (OutputSpec), same as every provider.
"""

from __future__ import annotations

from google import genai
from google.genai import types

from ai_image_creator.models import ImageRequest
from ai_image_creator.providers.base import GeneratedImage


class GeminiProvider:
    def __init__(self, client: genai.Client) -> None:
        # Injected so tests can pass a mock (Inject-Collaborators rule).
        self._client = client

    def generate(self, request: ImageRequest) -> list[GeneratedImage]:
        assert request.size is not None  # resolved by ImageRequest validator
        if request.model.startswith("imagen"):
            return self._generate_imagen(request)
        return self._generate_content(request)

    def _generate_imagen(self, request: ImageRequest) -> list[GeneratedImage]:
        size = request.size
        assert size is not None
        response = self._client.models.generate_images(
            model=request.model,
            prompt=request.prompt,
            config=types.GenerateImagesConfig(
                number_of_images=request.n,
                aspect_ratio=size,
            ),
        )
        generated = response.generated_images
        if not generated:
            return []
        return [
            GeneratedImage(data=self._imagen_bytes(item), source_size=size) for item in generated
        ]

    def _generate_content(self, request: ImageRequest) -> list[GeneratedImage]:
        size = request.size
        assert size is not None
        # generate_content yields one image per call; loop to honour `n`.
        config = types.GenerateContentConfig(
            response_modalities=["IMAGE"],
            image_config=types.ImageConfig(aspect_ratio=size),
        )
        images: list[GeneratedImage] = []
        for _ in range(request.n):
            response = self._client.models.generate_content(
                model=request.model,
                contents=request.prompt,
                config=config,
            )
            images.append(GeneratedImage(data=self._content_bytes(response), source_size=size))
        return images

    @staticmethod
    def _imagen_bytes(item: object) -> bytes:
        image = getattr(item, "image", None)
        data = getattr(image, "image_bytes", None)
        if data:
            return bytes(data)
        raise ValueError("Gemini imagen item had no image_bytes")

    @staticmethod
    def _content_bytes(response: object) -> bytes:
        candidates = getattr(response, "candidates", None) or []
        for candidate in candidates:
            content = getattr(candidate, "content", None)
            for part in getattr(content, "parts", None) or []:
                inline = getattr(part, "inline_data", None)
                data = getattr(inline, "data", None)
                if data:
                    return bytes(data)
        raise ValueError("Gemini response had no inline image data")
