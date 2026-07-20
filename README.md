# AI Image Creator

Create images with AI providers from the command line. Feed it a **JSON batch
file** or a few **CLI arguments**. Providers: **OpenAI** and **Google Gemini**;
the provider layer is pluggable so more can be added later.

## Features

- Batch generation from a JSON list of requests.
- Single image straight from CLI arguments.
- Provider generation `size` validated against the model (fails fast if invalid).
- Separate `output` step: resize/crop the result to **any** width/height with a
  chosen crop mode (`center`, `top`, `bottom`, `left`, `right`, `stretch`).

## Requirements

- [uv](https://docs.astral.sh/uv/)
- An OpenAI and/or Google Gemini API key (whichever provider you use)

## Install

```bat
install.bat
```

Then copy `.env.example` to `.env` and set your key:

```
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=...
```

Set only the key(s) for the provider(s) you use. All env vars: [docs/ENV.md](docs/ENV.md).

## Usage

Batch from a JSON file:

```bat
uv run ai-image-creator examples\requests.json
```

Single image from arguments:

```bat
uv run ai-image-creator --prompt "a red fox in snow" --model gpt-image-1 ^
    --size 1024x1024 --output output\fox.png --width 800 --height 600 --crop center
```

`--api-key` overrides the environment. Run `uv run ai-image-creator -h` for all flags.

## JSON format

The file is a **list** of request objects:

```json
[
  {
    "prompt": "a red fox in deep snow",
    "provider": "openai",
    "model": "gpt-image-1",
    "size": "1024x1024",
    "n": 1,
    "quality": "high",
    "output": {
      "path": "output/fox.png",
      "width": 800,
      "height": 600,
      "crop": "center",
      "format": "png"
    }
  }
]
```

| Field     | Required | Default            | Notes                                             |
|-----------|----------|--------------------|---------------------------------------------------|
| `prompt`  | yes      | —                  | Non-empty.                                        |
| `provider`| no       | `openai`           |                                                   |
| `model`   | no       | `gpt-image-2`      | Newest by default.                                |
| `size`    | no       | model default      | Must be valid for the model, else rejected.       |
| `n`       | no       | `1`                | Images per request.                               |
| `quality` | no       | provider default   | e.g. `high` for gpt-image-1.                      |
| `output`  | no       | save raw as-is     | Post-processing block (below).                    |

`output`: `path` required; `width`+`height` must be set together (any positive
values); `crop` ∈ the modes above; `format` e.g. `png` / `jpg`. When `n > 1`, an
index is inserted into the filename (`fox_0.png`, `fox_1.png`, …).

## Supported models & sizes

| Model                   | Valid sizes                             |
|-------------------------|-----------------------------------------|
| `gpt-image-2` (default) | 1024x1024, 1024x1536, 1536x1024, auto   |
| `gpt-image-1`           | 1024x1024, 1024x1536, 1536x1024, auto   |
| `dall-e-3`              | 1024x1024, 1792x1024, 1024x1792         |
| `dall-e-2`              | 256x256, 512x512, 1024x1024             |
| `gemini-2.5-flash-image`| 1:1, 3:4, 4:3, 9:16, 16:9 (aspect ratios) |
| `imagen-4.0-generate-001` / `-ultra-` / `-fast-` | 1:1, 3:4, 4:3, 9:16, 16:9 (aspect ratios) |

Gemini/Imagen `size` is an **aspect ratio**, not pixels — the final pixel size
comes from the `output` block. Provider details:
[docs/models/OPEN_AI.md](docs/models/OPEN_AI.md),
[docs/models/GEMINI.md](docs/models/GEMINI.md).
Config reference: [docs/CONFIG.md](docs/CONFIG.md) · [docs/ENV.md](docs/ENV.md).

## Tests

```bat
tools\run_tests.bat              REM unit tests (no network)
tools\run_integration_tests.bat  REM batch runner through a fake provider
```

## Dependencies

`openai`, `google-genai`, `pydantic`, `pillow`, `python-dotenv`. Dev: `pytest`,
`ruff`, `mypy`.
