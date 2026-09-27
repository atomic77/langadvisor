# LangAdvisor — Agent Guide

## Project Overview

LangAdvisor is a **Flet desktop GUI** application (also runnable as a web server) — a toolkit for language learners and polyglots powered by local and cloud LLMs via [Ollama](https://ollama.com/). It provides four modes plus a settings panel:

- **Assessment (grammar)** — the user pastes text, picks a language and formality level, and receives a grammaticality verdict (`yes`/`no`) with optional feedback and a corrected suggestion.
- **Practice** — generates a phrase in the target language at a chosen CEFR (mislabeled "ECTS" in the UI) level and category; the user's English translation is graded.
- **Lesson** — a multi-step round of phrases generated in bulk, answered one at a time, and batch-graded at the end with a score and summary.
- **Translation** — produces `N` distinct translations (with short tags like "literal"/"idiomatic") of a source text into a target language, including an "Auto-detect" source option.
- **Settings** — global default model, enabled languages, and accessibility (font family + size scale).

## Runtime & Tooling

**Primary runtime: `uv`** — all Python commands should be run via `uv run`, not bare `python` or `pip`.

| Task | Command |
|---|---|
| Install / sync dependencies | `uv sync` |
| Run the application | `uv run python main.py` |
| Run the tests | `uv run pytest tests/ -v` |
| Add a dependency | `uv add <package>` |

A virtual environment is managed by `uv` under `.venv/`, and the project ships a pre-populated `uv.lock`.

### Running as a web server

The same app can be hosted for multiple users over the web (Ollama must run on the host):

```bash
FLET_FORCE_WEB_SERVER=true FLET_SERVER_PORT=8008 uv run python main.py
```

## Project Structure

```
langadvisor/
├── main.py                  # Entry point — ft.app(target=main)
├── ui/
│   ├── app.py               # Page layout, mode switching, service wiring, keyboard shortcuts
│   ├── sidebar.py           # Collapsible sidebar: nav links, history list, search, theme toggle
│   ├── assessment_panel.py  # Grammar mode: text input, language/formality dropdowns, results
│   ├── practice_panel.py    # Practice mode: generate phrase → translate → check/help
│   ├── lesson_panel.py      # Lesson mode: 5-state wizard (setup/generating/practicing/reviewing/results)
│   ├── translation_panel.py # Translation mode: source input + N variant results
│   ├── settings_panel.py    # Default model, language selection dialog, accessibility
│   ├── controls.py          # Shared dropdown factories + option lists (formality/category/ECTS)
│   └── typography.py        # App-wide font-scaling helpers
├── core/
│   ├── llm.py               # All LLM prompts + parsers (grammar, practice, translation, grading)
│   ├── languages.py         # TOP_50_LANGUAGES list + DEFAULT_ENABLED_LANGUAGES
│   ├── history_store.py     # Observable in-memory assessment history (HistoryEntry)
│   ├── lesson_store.py      # Observable in-memory lesson rounds (LessonEntry)
│   ├── persistence.py       # SQLite (history, settings, lesson_rounds tables)
│   ├── model_fetcher.py     # Ollama model discovery via the `ollama` Python client
│   └── paths.py             # platformdirs-based config/data directory resolution
├── services/
│   ├── assessor.py          # Grammar assessment orchestration
│   ├── practice_service.py  # Practice generate/check/help orchestration
│   ├── lesson_service.py    # Lesson round state machine + batched grading
│   └── translation_service.py # Translation orchestration (not persisted to history)
└── tests/                   # pytest + pytest-asyncio; ChatOllama fully mocked
```

## Key Components

### UI Layer (`ui/`)

- **`app.py`** — `main(page)` wires everything together. Dark theme by default. Holds a single `content_area` and swaps panels via `_switch_mode(mode)` for `"grammar" | "practice" | "lesson" | "translation" | "settings"`. Registers `Ctrl+Enter` (mode-sensitive: assess / lesson-next / translate). Spawns a **daemon thread** to discover Ollama models, marshalling results back to the Flet thread via `page.run_thread(...)`.
- **`sidebar.py`** — `Sidebar` widget with collapsed/expanded states. Navigation links for all five modes, a history list (grammar mode only) with search + clear, and a dark/light theme toggle. Contextual content (stats, topics) is stubbed out; only the history list is functional.
- **`*_panel.py`** — each panel encapsulates its own Flet controls and exposes `view`, a `set_languages(...)` method (shared dropdown contract), and mode-specific state setters. **Model selection is a global Settings default**, not per-panel; services call `core.llm.get_default_model()` directly (panels no longer carry a `selected_model` property). Formality / category / CEFR-level dropdowns are built from shared factories in `ui/controls.py`.

### Core Layer (`core/`)

- **`llm.py`** — the LLM interaction layer. `get_llm(model)` returns a **cached** `ChatOllama` (singleton, `temperature=0`) that resolves to the module-level `_default_model` when no model is passed. Public async functions:
  - `check_grammar(text, language, formality, model)` → `(verdict, feedback, suggestion)` — yes/no verdict, then feedback+suggestion if "no".
  - `get_feedback_and_suggestion(...)` — FEEDBACK:/SUGGESTION: prompt.
  - `generate_practice_sentence(...)` → `(phrase, translation[, romanization])` — single phrase.
  - `check_translation(...)` → mistakes string.
  - `translate_text(...)` → list of `(translation, tag)` variants.
  - `generate_practice_set(...)` → list of phrases for a Lesson round.
  - `grade_practice_batch(...)` → `(overall_summary, [per-item dicts])` — single-call batch grading.
  - Private `_parse_*` helpers parse the structured model output (tolerating continuation lines, missing indices, and malformed responses). Two generic helpers back them: `_parse_numbered` (numbered FIELD: value lists, used by translation and practice-set parsing) and `_parse_labeled_blocks` (single-block FIELD: sections, used by feedback/phrase/mistakes parsing). `phrase_text` / `phrase_reference` / `phrase_romanization` safely index the variable-length `PracticePhrase` tuple and are reused by the services. A `_ROMANIZATION_SCHEMES` dict maps non-Latin-script languages to their standard romanization schemes.
- **`languages.py`** — `TOP_50_LANGUAGES` (actually a large curated list including modern European languages and many historical/reconstructed languages) and `DEFAULT_ENABLED_LANGUAGES` (`["English", "Serbian", "Italian", "French", "Japanese"]`).
- **`history_store.py`** — `HistoryEntry` dataclass + observable `HistoryStore` (change callbacks, newest-first, delegates to SQLite).
- **`lesson_store.py`** — `LessonEntry` dataclass + observable `LessonStore`, mirrors `HistoryStore`.
- **`persistence.py`** — SQLite with three tables: `history`, `settings` (key/value), and `lesson_rounds`. All `load_*`/`save_*` helpers accept an optional `db_path` for testability. Settings persist the default model, enabled languages (JSON-encoded), and UI font scale/family. Schema created on first connect via `_ensure_db`.
- **`model_fetcher.py`** — `fetch_ollama_models()` calls `ollama.list()` and returns sorted model names.
- **`paths.py`** — `HISTORY_DB = data_dir() / "history.db"` via `platformdirs` (data-dir only; settings live in SQLite).

### Service Layer (`services/`)

Each service coordinates LLM calls, panel state, and (where applicable) persistence, and supports **cancelling** an in-flight request (second click cancels the running `asyncio.Task`).

- **`assessor.py`** — `AssessorService`. Runs `check_grammar`, updates the panel, and appends a `HistoryEntry` to the store.
- **`practice_service.py`** — `PracticeService`. `on_generate`, `on_check`, `on_help`; stashes the reference translation for the Help button.
- **`lesson_service.py`** — `LessonService`. A state machine (`setup → generating → practicing → reviewing → results`) driving `LessonPanel`. Generates a batch, pads short batches with single-phrase retries, collects answers across navigation, batch-grades on submit, and persists a `LessonEntry`.
- **`translation_service.py`** — `TranslationService`. Calls `translate_text` and renders variants; intentionally does **not** persist to history.

### Tests (`tests/`)

- `pytest` + `pytest-asyncio`; `ChatOllama` is mocked (`AsyncMock`), `ConnectError`/generic exceptions exercised.
- `test_main.py` — grammar LLM logic, history store, model fetcher, sidebar search.
- `test_translation.py` — `_parse_translations` + `translate_text`.
- `test_lesson.py` — practice/lesson parsers, batch grading, `LessonService` state machine.
- `test_persistence.py` — SQLite round-trips using `tmp_path`.
- `test_languages.py` — language list contents.
- `test_paths.py` — platformdir mocking.
- A `reset_llm_globals` autouse fixture resets the module-level LLM cache before each test. **96 tests pass.**

## UI / Theme / Accessibility

The app defaults to **dark mode** (`ft.ThemeMode.DARK`); the sidebar toggles dark ↔ light. Accessibility controls (Settings panel) set a global **font family** and **font size scale** (0.9–1.6). `ui/typography.py` (`clamp_font_scale`, `scale_control_fonts`) applies the scale recursively while preserving each control's baseline size; panels implement `apply_typography(scale)` where width adjustments are needed. Colour constants use Flet's `ft.Colors` semantic tokens.

## Adding a Language, Formality, or Category

- **Languages** are sourced from `TOP_50_LANGUAGES` in `core/languages.py`; the enabled subset is chosen in the Settings dialog and pushed to every panel via `set_languages(...)` (which delegates to `ui.controls.set_dropdown_languages`). Add a language by appending to that list (and, if non-Latin-script, optionally a `_ROMANIZATION_SCHEMES` entry in `core/llm.py`).
- **Formality** options (`Colloquial` / `Business` / `Formal`), **practice/lesson categories**, and **CEFR levels** (`A1`–`C2`) all live in `ui/controls.py` (`FORMALITY_OPTIONS`, `CATEGORY_OPTIONS`, `ECTS_LEVEL_OPTIONS`) and are consumed by every panel via the `formality_dropdown` / `category_dropdown` / `ects_dropdown` factories — a one-file edit. CEFR level descriptions used in prompts live in `_ECTS_LEVELS` in `core/llm.py`.

## Ollama Compatibility & Models

Requires a running Ollama instance with at least one pulled model (local, e.g. `ollama pull llama3.2`, or an [Ollama Cloud](https://docs.ollama.com/cloud) account). Model discovery runs on startup in a background thread; if Ollama is unavailable, the Settings default-model dropdown is empty and a status message is shown. Recommended models are documented in `README.md` (free tier vs. paid tier). The app itself only needs a model name — it does not hard-code any particular model.

## Build & Release

`.github/workflows/build-release.yml` builds and publishes releases via `uv run flet build`. It currently targets **Windows x64** and **Linux x64** only; macOS and Linux arm64 builds are commented out (see the in-file TODOs). Triggered on a `v*` tag push or via `workflow_dispatch` with an existing tag. Builds are zipped and published to a GitHub Release with generated notes. `build/` is git-ignored.
