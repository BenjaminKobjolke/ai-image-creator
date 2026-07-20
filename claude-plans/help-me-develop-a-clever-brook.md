# Plan: AI Image Creator (Python CLI)

## Context

Greenfield tool. Generate images via AI providers from the CLI. Two input modes:
a **JSON file** describing a batch of image requests, or **CLI arguments** for a
single quick request. First provider is **OpenAI**; more providers later, so the
provider layer is pluggable by name. Repo is empty; everything below is new.

Adheres to COMMON/AI/PYTHON rules: uv + `pyproject.toml`, Pydantic validation at
the JSON boundary, one central `AppLogger`, typed DTOs (no bag-of-keys), argparse
(stdlib over a CLI dep), files < 300 lines, tests with no network.

### Key design decisions (from user)

- **Default model = newest** (`gpt-image-1`); overridable per-request via JSON or via CLI.
- **Input JSON = a list** (batch). CLI single-request mode builds a 1-item batch and
  runs the same path.
- **Two size concepts, kept separate:**
  - `size` = what the provider generates. **Rejected at validation** if not a valid
    size for the chosen model (fail fast, clear message).
  - `output` = desired final file: any `width`/`height` + `crop` mode. Achieved by
    post-processing the generated image with Pillow (resize + crop). Optional — if
    omitted, the provider image is saved as-is.

## New dependencies (confirm latest stable before adding — Confirm-Versions rule)

- `openai` — OpenAI SDK (Images API)
- `pydantic` — request/output validation
- `pillow` — output resize + crop
- `python-dotenv` — load `OPENAI_API_KEY` from `.env`
- dev: `pytest`, `ruff`, `mypy`

## JSON schema (a list of requests)

```json
[
  {
    "prompt": "a red fox in deep snow, cinematic",
    "provider": "openai",
    "model": "gpt-image-1",
    "size": "1024x1024",
    "n": 1,
    "quality": "high",
    "output": {
      "path": "out/fox.png",
      "width": 800,
      "height": 600,
      "crop": "center",
      "format": "png"
    }
  }
]
```

- `prompt` required. `provider` defaults `openai`, `model` defaults newest,
  `size` defaults the model's default, `n` defaults 1.
- `output` optional. `output.path` required when `output` present (else a default
  path is generated: `output/<index>_<n>.png`). `crop` ∈ `center|top|bottom|left|right|stretch`.
  `stretch` = plain resize (ignore aspect); the anchors = cover-crop via
  `PIL.ImageOps.fit(centering=...)`.

## CLI

```
# batch from JSON
uv run ai-image-creator requests.json

# single request via args (builds a 1-item batch)
uv run ai-image-creator --prompt "a red fox" --model gpt-image-1 \
    --size 1024x1024 --output out/fox.png --width 800 --height 600 --crop center
```

`argparse` (stdlib). A positional `json_path` XOR `--prompt`. `--api-key` overrides env.

## File layout (each file < 300 lines)

```
ai_image_creator/
  __init__.py
  __main__.py            # `python -m ai_image_creator` -> cli.main()
  cli.py                 # argparse; build batch from JSON file OR from args; call runner
  constants.py           # string constants; VALID_SIZES per model; defaults; crop-mode strings
  settings.py            # Settings dataclass: OPENAI_API_KEY, default provider/model (env-driven, dotenv)
  app_logger.py          # AppLogger wrapping stdlib logging (single toggle) — mandated name/file
  models.py              # Pydantic: ImageRequest, OutputSpec, CropMode(str Enum); size validator
  runner.py              # orchestrate batch: for each req -> provider.generate -> process -> save; collect results
  providers/
    __init__.py
    base.py              # ImageProvider Protocol: generate(req) -> list[GeneratedImage]; GeneratedImage(bytes)
    registry.py          # name -> provider factory (build_provider(name, settings))
    openai_provider.py   # OpenAIProvider: call images API, normalize b64/url -> raw PNG bytes
  processing/
    __init__.py
    image_output.py      # resize_and_crop(bytes, OutputSpec) -> bytes ; save(bytes, path)
tests/
  unit/
    test_models.py       # valid/invalid size rejected per model; defaults applied
    test_image_output.py # center-crop/stretch produce exact WxH; anchor -> centering map
    test_registry.py     # known name -> provider; unknown -> clear error
    test_openai_provider.py  # MagicMock(spec=OpenAI): b64 + url normalization, no network
  integration/
    test_batch_runner.py # runner end-to-end through a FAKE provider (registered) -> files written, no network
tools/
  run_tests.bat          # pytest tests/unit -v
  run_integration_tests.bat  # pytest tests/integration -v
start.bat                # uv run ai-image-creator %*
install.bat              # uv sync --all-extras + tests
update.bat               # uv lock --upgrade + ruff/mypy + tests
pyproject.toml           # single source of truth; console_script entry = ai_image_creator.cli:main
uv.lock
.env.example             # OPENAI_API_KEY=
README.md                # name, install, usage (both modes), JSON schema, deps
CLAUDE.md                # COMMON + AI + PYTHON rules copied in (Keep-in-Sync rule)
.gitignore               # .venv, __pycache__, .env, output/
```

## Component notes

- **models.py** — `ImageRequest` (Pydantic) validates one request. A field/model
  validator checks `size` against `constants.VALID_SIZES[model]` and raises a clear
  `ValueError` when invalid (reject, per decision). `OutputSpec` validates
  `width>0/height>0` and `crop` enum. `n>=1`. Missing `model` -> newest default.
- **providers/base.py** — `ImageProvider` Protocol with one method returning a typed
  `GeneratedImage` (raw bytes + source size), never a dict (No-Bag-of-Keys). Justified
  over YAGNI by the explicit "more providers later" requirement; kept to one small method.
- **openai_provider.py** — uses injected `OpenAI` client (constructor-injected, so tests
  mock it; Inject-Collaborators rule). `gpt-image-1` returns `b64_json` -> decode;
  dall-e url -> download bytes. Output: raw PNG bytes.
- **image_output.py** — `stretch` = `img.resize((w,h))`; anchors = `ImageOps.fit(img,(w,h),
  centering=ANCHOR_MAP[crop])`. One function covers all anchors. Pure, no I/O except `save`.
- **runner.py** — the only orchestration; sequential. `# ponytail: sequential batch;
  swap to AsyncOpenAI + asyncio.gather if batch latency matters`. Returns a typed
  result list (path, ok, error) for CLI summary.
- **app_logger.py** — `AppLogger` wraps stdlib `logging`; level from `Settings`. All
  modules log through it, never `print`.

## Verification (end-to-end)

1. `install.bat` -> `uv sync` succeeds, unit tests green.
2. Unit: `tools/run_tests.bat` — size-rejection, crop dimensions exact, provider
   normalization (mocked), registry. No network.
3. Integration: `tools/run_integration_tests.bat` — batch runner writes N files at the
   requested output dimensions through a **fake** provider (no API call).
4. Real smoke (manual, needs key): set `OPENAI_API_KEY` in `.env`, run
   `uv run ai-image-creator --prompt "a red fox in snow" --output out/fox.png --width 800 --height 600 --crop center`
   -> confirm `out/fox.png` exists and is exactly 800x600.
5. Batch smoke: run with a 2-item `requests.json` -> two files, correct sizes, summary logged.

## Post-plan rule chain (AI_RULES)

After approval: `/plan:dry` -> `/plan:dry-checked` -> `/convention:check` -> implement ->
`/dry:check` -> `/verify:after-change`.
