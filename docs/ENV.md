# Environment Variables

All configuration comes from a central `Settings` (`ai_image_creator/settings.py`),
loaded from the environment or a `.env` file (via `python-dotenv`). Names live in
`ai_image_creator/constants.py`. Copy `.env.example` to `.env` and fill in. **Never
commit `.env`** (git-ignored).

| Variable                       | Required | Default | Purpose |
|--------------------------------|----------|---------|---------|
| `OPENAI_API_KEY`               | for OpenAI provider | — | OpenAI API key. |
| `GEMINI_API_KEY`               | for Gemini provider | — | Google Gemini API key. |
| `AI_IMAGE_CREATOR_LOG_LEVEL`   | no       | `INFO`  | `DEBUG` \| `INFO` \| `WARNING` \| `ERROR`. |

Set only the API key(s) for the provider(s) you actually use.

## API key resolution

Each provider key resolves in this order (first match wins):

1. `--api-key` CLI flag — applied to **both** `OPENAI_API_KEY` and `GEMINI_API_KEY`,
   so one flag works for whichever provider the request selects.
2. The environment variable.
3. The value in `.env`.

`build_provider` raises a clear error naming the missing variable if the selected
provider has no key. Keys are never logged.

## Example `.env`

```
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=...

# Optional
AI_IMAGE_CREATOR_LOG_LEVEL=INFO
```
