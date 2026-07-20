@echo off
echo Upgrading lockfile...
uv lock --upgrade
if errorlevel 1 exit /b 1
uv sync --all-extras
if errorlevel 1 exit /b 1
echo Linting...
uv run ruff check .
uv run ruff format --check .
uv run mypy ai_image_creator
echo Running tests...
uv run pytest tests/unit -v
