# Plan — Add Google Gemini provider

## Context

Project generates images via pluggable providers; only OpenAI exists today
(`docs/models/OPEN_AI.md`). Goal: add Google Gemini as a second provider so a
batch JSON / CLI request can pick a Gemini model. Provider layer is already
name-dispatched (`registry.build_provider`), so this is additive.

Two facts shape the design:

1. **Gemini uses aspect ratios, not pixel sizes.** OpenAI `size` = `1024x1024`;
   Gemini/Imagen `size` = an aspect ratio like `1:1`, `16:9`. The size validator
   (`models._resolve_and_validate_size`) is a **membership check keyed by model**,
   not a `WxH` parser — so aspect-ratio strings slot into `VALID_SIZES` with **no
   validator change**. Final on-disk pixels are still handled by the provider-
   independent Pillow step (`processing/image_output.py`, `OutputSpec`).
2. **Two Gemini API shapes.** `gemini-2.5-flash-image` uses `generate_content`;
   `imagen-*` uses `generate_images`. Both are added; the provider routes by model
   id. (Note: Imagen models are deprecated by Google, shutdown **2026-08-17** —
   documented, not blocked, since the user wants model choice in JSON.)

Decisions (from user): support multiple Gemini models, chosen per-request in JSON;
both API keys settable via env; the `--api-key` CLI flag feeds **both** providers.

## Changes

### 1. `ai_image_creator/constants.py`
- Add `PROVIDER_GEMINI = "gemini"`.
- Add `ENV_GEMINI_API_KEY = "GEMINI_API_KEY"`.
- Add model constants: `MODEL_GEMINI_25_FLASH_IMAGE = "gemini-2.5-flash-image"`,
  `MODEL_IMAGEN_4 = "imagen-4.0-generate-001"`,
  `MODEL_IMAGEN_4_ULTRA = "imagen-4.0-ultra-generate-001"`,
  `MODEL_IMAGEN_4_FAST = "imagen-4.0-fast-generate-001"`.
- Extend `VALID_SIZES` for each new model with aspect ratios:
  `("1:1", "3:4", "4:3", "9:16", "16:9")`.
- Extend `DEFAULT_SIZE` with `"1:1"` for each new model.
- (No change to `DEFAULT_PROVIDER` / `DEFAULT_MODEL` — OpenAI stays default.)

### 2. `ai_image_creator/settings.py`
- Add field `gemini_api_key: str | None`.
- In `Settings.load`, resolve it as `api_key_override or os.getenv(ENV_GEMINI_API_KEY)`
  — same override applied to `openai_api_key`, so `--api-key` feeds both.

### 3. `ai_image_creator/providers/gemini_provider.py` (new, <300 lines)
Mirror `OpenAIProvider`: injected client, implement
`generate(request: ImageRequest) -> list[GeneratedImage]`.
- Route by model id: `imagen-*` → `client.models.generate_images(model, prompt,
  config=GenerateImagesConfig(number_of_images=n, aspect_ratio=size))`, extract
  `resp.generated_images[i].image.image_bytes`.
- else (`gemini-*`) → `client.models.generate_content(model, contents=prompt,
  config=GenerateContentConfig(response_modalities=["IMAGE"],
  image_config=ImageConfig(aspect_ratio=size)))`, extract first inline image bytes
  from `resp.candidates[0].content.parts[*].inline_data.data`. `generate_content`
  yields 1 image/call, so loop `request.n` times to honor `n`.
- Each result → `GeneratedImage(data=<bytes>, source_size=request.size)`.
- `quality` ignored (OpenAI-only). Empty/missing image → return `[]` (mirror
  OpenAI's empty-data behavior); a part with no image data raises `ValueError`.
- Exact SDK attribute names (`image_bytes` vs `inline_data.data`, config type
  locations under `google.genai.types`) verified against the installed
  `google-genai` during implementation.

### 4. `ai_image_creator/providers/registry.py`
- Add `elif name == constants.PROVIDER_GEMINI:` branch — check
  `settings.gemini_api_key` (raise `ValueError` naming `ENV_GEMINI_API_KEY` if
  missing), lazy-import `from google import genai`, return
  `GeminiProvider(genai.Client(api_key=settings.gemini_api_key))`.
- Update the final "unknown provider" error to list both provider names.

### 5. `pyproject.toml`
- Add `google-genai` to `dependencies`. Confirm latest stable version with user
  before `uv add` (Confirm-Dependency-Versions rule).

### 6. `ai_image_creator/cli.py`
- Update `--api-key` help text: overrides `OPENAI_API_KEY` **and** `GEMINI_API_KEY`.
  (No other CLI change needed — `--provider` is already a free string routed via
  `runner._get_provider`.)

### 7. Docs
- New `docs/models/GEMINI.md` mirroring `OPEN_AI.md` (auth, models+aspect-ratio
  table, request mapping, response normalization, Imagen deprecation note).
- README: mention the second provider.

## Tests (TDD — write first, confirm red, implement)
- `tests/unit/test_gemini_provider.py` — mirror `test_openai_provider.py`:
  `MagicMock(spec=genai.Client)`, stub `generate_content` and `generate_images`
  return shapes with `SimpleNamespace`, assert `.data` bytes + `.source_size`, and
  that `n>1` on a `gemini-*` model loops N calls. Include a no-image → `ValueError`
  case.
- `tests/unit/test_registry.py` — add `test_gemini_provider_built` +
  missing-key-raises; **update the positional `_settings(...)` helper** for the new
  `gemini_api_key` field.
- `tests/unit/test_models.py` — add a case asserting a Gemini model + aspect-ratio
  size validates, and a bad size for a Gemini model is rejected.

## Verification
1. `install.bat` (uv sync + unit tests) or `tools\run_tests.bat` — all green.
2. `uv run mypy` (strict) + `ruff check` — clean.
3. Manual end-to-end (needs `GEMINI_API_KEY`):
   `uv run ai-image-creator --provider gemini --model gemini-2.5-flash-image
   --prompt "a red bicycle" --size 16:9` → image written; then an `imagen-4.0-*`
   run to exercise the second path.
4. Confirm an OpenAI request still works unchanged (no regression).
