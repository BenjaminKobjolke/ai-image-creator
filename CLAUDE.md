# CLAUDE.md — AI Image Creator

CLI tool to generate images via AI providers. Input: a JSON batch file **or** CLI
arguments. First provider: OpenAI. Provider layer is pluggable by name.

## Architecture

```
ai_image_creator/
  cli.py            argparse; JSON file XOR --prompt -> list[ImageRequest] -> runner
  models.py         ImageRequest / OutputSpec / CropMode (Pydantic); size validation
  constants.py      provider names, VALID_SIZES per model, defaults, env var names
  settings.py       env-driven Settings (dotenv)
  app_logger.py     AppLogger (central logging)
  runner.py         sequential batch: generate -> post-process -> save; typed results
  providers/
    base.py         ImageProvider Protocol + GeneratedImage DTO
    registry.py     build_provider(name, settings)
    openai_provider.py  OpenAI Images API; b64/url -> bytes; injected client
  processing/
    image_output.py resize_and_crop (ImageOps.fit anchors / stretch) + save
```

Two size concepts, kept separate: `size` = what the provider generates (rejected
if invalid for the model); `output` = final file on disk (any width/height + crop,
done with Pillow). Default model = `gpt-image-2` (newest); overridable per request.

## Adding a provider

1. New module in `providers/` implementing `ImageProvider.generate`.
2. Add a branch in `providers/registry.py` and a name constant in `constants.py`.
3. Add its models + valid sizes to `VALID_SIZES` / `DEFAULT_SIZE`.

## Commands

```bat
install.bat                      REM uv sync + unit tests
tools\run_tests.bat              REM unit tests
tools\run_integration_tests.bat  REM integration tests
uv run ai-image-creator -h       REM CLI help
```

## AI workflow (after a plan is approved)

`/plan:dry` → `/plan:dry-checked` → `/convention:check` → implement →
`/dry:check` → `/verify:after-change`. Bug fixes: `bugs:fix` → `/verify:after-change`.

---

# Coding Rules (inlined)

Canonical source: `D:\GIT\BenjaminKobjolke\claude-code\coding-rules\`. Copied here
so they travel with the project (Keep-CLAUDE.md-in-Sync rule). If the canonical
files change, re-sync.

---

## Common Rules (All Languages)

### Use Objects for Related Values

When multiple related values must be passed between classes or methods, bundle them
into a dedicated object (DTO/Settings/Config) instead of passing many parameters.

### No Bag-of-Keys Returns at Module Boundaries

Public methods that return data crossing a module boundary must return a typed object
(DTO, value object, or domain model) — never a raw dict indexed by string keys. Plain
`array`/`dict` returns silently swallow shape bugs. Lists vs single must be obvious from
the type (`getThing(): ?Thing` vs `getThings(): ThingList`). Distinguish absent (`None`)
from empty. JSON-decoded blobs are dicts too — wrap them before they leave the owning
layer. Pure-private dict juggling inside one method is fine.

### Reuse Existing Models Before Inventing Array Shapes

Before designing a new DTO, search for an existing domain class that already owns the
same data. Grep for the table name, primary key, distinctive column. Adding
`getXxxObject()` alongside a legacy `getXxxData()` is acceptable as a migration step;
delete the array version once consumers migrate.

### Tests Pin the Shape Before the Refactor

When converting a bag-of-keys return to a typed object, write a characterization test
first, run it green against the unrefactored code, then refactor. Same test stays green.

### Test-Driven Development for Features and Bug Fixes

1. Write tests first. 2. Confirm they fail. 3. Implement. 4. Confirm they pass.

### Integration Tests

Every project includes integration tests in addition to unit tests.

### Test Runner Scripts

Provide `tools/run_tests.bat` (unit) and `tools/run_integration_tests.bat` (integration).

### Prefer Type-Safe Values

Use strong, explicit types (typed DTOs, enums, generics, typed settings) over loosely/
stringly typed values.

### String Constants

Centralize string constants in a dedicated module/class. Do not scatter raw strings.

### Reusable Tooling

Before building project-specific infra scripts, check the language's `*_setup_files/`
folder for an existing equivalent. If found, copy/reference it. If not: build + prove it,
copy into `*_setup_files/tools/`, document it in the language `*_RULES.md`.

### README.md is Mandatory

Root `README.md` with: project name/description, install/setup, usage examples,
dependencies/requirements.

### Don't Repeat Yourself (DRY)

Avoid duplication. Extract shared logic into a reusable function/class/module/utility.
Use constants for repeated values.

### Derive, Don't Duplicate — One Value Owns the Derivation

When one value strictly determines another, pass only the determinant and derive the
rest — never thread both. The richer type owns the relationship (e.g.
`ActionType::category()`). Apply only for true functional dependencies; keep derivation
cheap/pure and the mapping exhaustive (enum + exhaustive match).

### Keep It Simple (KISS)

Prefer the simplest solution that works. YAGNI (no interface with a single impl, no
factory for one product, no config for a constant). Boring over clever. Deletion over
addition.

### Confirm Dependency Versions

Before adding any package, confirm the latest stable version with the user. Don't assume.
Avoid outdated packages.

### Error Handling & Logging Strategy

Centralized error handler, not ad-hoc try/catch everywhere. Structured logging (not
`print`). Levels: debug/info/warning/error. Include context (module, operation, IDs).

### Centralized Logger — Single Off Switch

Route all logging through one logger class/module. Never call built-in output for logging
directly. One toggle for enable/level/redirect. Callers pass a level; the logger decides
what emits. Python: `AppLogger` in `app_logger.py`.

### Input Validation at Boundaries

Validate data at system boundaries (API inputs, user input, files, external responses).
Never trust external data. Use Pydantic/Zod/etc. Fail fast with clear messages.

### Maximum File Length — 300 Lines

Split files over 300 lines. Extract classes/functions/components. Exceptions: generated,
config, test files with many similar cases.

### Naming Conventions

Files `snake_case` (or language convention), Classes `PascalCase`, Constants
`UPPER_SNAKE_CASE`, functions/variables per language convention (`snake_case` for Python).

### Comments Explain Why, Not What

Comment intent and non-obvious reasoning, not a restatement of code. Document why a
workaround/algorithm exists or a non-local constraint. Keep comments in sync; delete stale.

### Security Baseline

Never commit secrets. Escape output. Parameterized queries / ORM. Validate + sanitize
input at boundaries. Keep dependencies updated.

### No Hardcoded Environment Values

Never hardcode paths, hostnames, IPs, ports, base URLs. Read from central config with a
committed `.example` template. This is about portability, distinct from secrecy.

### No God Classes

One responsibility per class. Warning signs: >5 public methods, >4 constructor deps, or
methods spanning unrelated domains. Split by responsibility. If you can't name it without
"Manager/Handler/Service/Helper", it likely does too much.

### Self-Describing Classes

When behavior depends on which fields a class has (search, serialization, display,
validation, auditing), the class declares those fields via a contract (interface/abstract
method/metadata/introspection). Never hardcode field lists in consumers.

### Inject Collaborators, Don't Fold Dependencies In

Prefer injected collaborators (single dependency, shared hub) over folding helpers
(mixins/traits) that merge all their deps into the host. Reserve fold-in for stateless,
dependency-free helpers.

- **Inject services; never `new` one inside a method** — hides the dependency and blocks
  test substitution. Pass collaborators through the constructor.
- **Collapse config-callback swarms into one value object** — bundle many one-line
  overridable getters into a single config object built once and handed to the base.

---

## AI Workflow Rules (All Languages, always apply)

### Feature / Change Workflow

After a plan is approved:

```
plan approved
  → /plan:dry            check approved plan for DRY/consolidation BEFORE code
  → /plan:dry-checked    reload + review the DRY-adjusted plan
  → /convention:check    scan for existing patterns/components to reuse
  ─────────────────────  DRY GATE — must be cleared to proceed
  → restate Definition-of-Done aloud
  → implement
  → /dry:check           post-implementation DRY audit
  → /verify:after-change run tests + code analysis
```

**DRY gate (precondition for implementing).** Do not write a line until all true, and
restate the gate aloud when you start implementing:
- [ ] `/plan:dry` ran and the plan was adjusted for any duplication found.
- [ ] `/plan:dry-checked` reloaded and confirmed the adjusted plan.
- [ ] `/convention:check` found the existing utilities/patterns to reuse.

The gate survives implementation: if you add a new helper/type/pattern mid-way, stop and
re-clear it.

**Definition of Done — restate aloud before implementing:** Scope (what changes / what
doesn't), Reuse (existing fn/component + path), DRY gate cleared, `/dry:check` clean,
`/verify:after-change` green.

**Post-implementation DRY audit template:**

```
DRY audit — <change name>
Changed files:     <list>
Duplication found: <none | describe>
Consolidated into: <shared fn/module + path | n/a>
Convention reused: <name + path>
Verdict:           <clean | needs rework>
```

### Bug-Fix Workflow

```
bugs:fix
  → /verify:after-change
```

### Optional Addons

Live in `ai_rules_addons/`, opt-in per project — ASK before wiring in (e.g.
`graphify.md`).

---

## Python Rules (uv)

### Template Engine

Keep Python/HTML/CSS/JS separated via Jinja2 (`uv add jinja2`). No JS in templates; use
separate `.js` files. Structure: `app/`, `templates/`, `static/{css,js}`.
*(Not applicable to this CLI — no web layer.)*

### GUI Framework

Desktop GUI = PySide6 (`uv add pyside6`), always latest. *(Not applicable — CLI.)*

### Localization

`python-localization` library (`D:\GIT\BenjaminKobjolke\python-localization`), editable
install via `uv add --editable`. `lang/*.json` nested; keys as `TK` constants; dot-notation
keys; `t(key, params)` with `:placeholder` params. *(Not applicable yet — CLI.)*

### Project Setup Scripts

Copy from `python_setup_files`: `install.bat` (uv check + `uv sync --all-extras` + tests),
`update.bat` (`uv lock --upgrade` + sync + ruff/mypy + tests), `tools/run_tests.bat`
(`pytest tests/ -v`, or `tests/unit`), `tools/run_integration_tests.bat`.

### Release Workflow

Set up with `/release:setup`. Label = `<version>_<build>` (version from `pyproject.toml`,
build integer in `build_version.txt`). Release notes = `release_notes/<version>_<build>/
<locale>.json`; author only `en.json`, generate other locales. Bundle `release_notes/`
into the build. In-app view newest-first with locale fallback to `en.json`.

### 8 Essential Rules

1. **`pyproject.toml` single source of truth.** No scattered config. Pin Python version;
   `uv add` deps; commit `uv.lock`.
2. **Enforce formatting + linting + typing in CI.** `uv add --dev ruff mypy`. CI runs
   `ruff check`, `ruff format --check`, `mypy`.
3. **Type hints on public APIs.** Typed params + returns. Use `Sequence`/`Mapping`/
   `Protocol`/`TypedDict`/`Literal`. Avoid `Any` except at I/O/third-party boundaries.
4. **Centralize config with env-driven settings.** Single `Settings` module; everything
   reads from it, not scattered `os.getenv`.
5. **Tests mandatory, fast, isolated.** pytest. No network in unit tests. tmp dirs/
   fixtures; no reliance on machine state.
6. **DB access uses SQLAlchemy ORM** (if a DB is needed). *(Not applicable.)*
7. **Use `spec=` with MagicMock** to catch interface mismatches. Mock methods as methods
   (`mock.get_body.return_value`), not fake attributes.
8. **Required batch files:** `start.bat` (root, starts app), `tools/run_tests.bat`.

### Async Patterns

`asyncio` for I/O-bound tasks. No blocking calls (`time.sleep`, sync HTTP) in async
contexts.

### Validation

Pydantic for request/data validation at API boundaries.

### Structured Logging

`structlog` or `logging` with JSON formatter — not `print()`. Route all logging through
one `AppLogger` (`app_logger.py`) wrapping the sink; feature code never calls
`logging.getLogger(...)` or `print()` directly.

### Self-Describing Classes (Python)

Protocol with an abstract method (`get_searchable_fields()`), or dataclass field
`metadata` + a `fields()` introspection helper. Prefer Protocol for simple cases.
