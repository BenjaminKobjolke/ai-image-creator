@echo off
where uv >nul 2>nul
if errorlevel 1 (
    echo uv is not installed. Install it from https://docs.astral.sh/uv/ and retry.
    exit /b 1
)
echo Syncing dependencies...
uv sync --all-extras
if errorlevel 1 exit /b 1
echo Running tests...
uv run pytest tests/unit -v
