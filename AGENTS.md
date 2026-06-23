# LangAdvisor — Agent Guide

## Project Overview

LangAdvisor is a **Flet desktop GUI** application for grammar assessment using local LLMs via [Ollama](https://ollama.com/). The user writes or pastes a text snippet, selects a language and formality level, picks an available Ollama model, and receives a grammaticality verdict (`yes`/`no`) with optional feedback and a corrected suggestion.

## Runtime & Tooling

**Primary runtime: `uv`** — all Python commands should be run via `uv run`, not bare `python` or `pip`.

| Task | Command |
|---|---|
| Install / sync dependencies | `uv sync` |
| Run the application | `uv run python main.py` |
| Run tests | `uv run pytest tests/ -v` |
| Add a dependency | `uv add <package>` |

A virtual environment is managed by `uv` under `.venv/`. The project ships a pre-populated `uv.lock`.

## Project Structure

```
langadvisor/
├── main.py              # Application entry point — flet.app() bootstrap
├── ui/
│   ├── app.py           # Page layout, theme, service wiring, keyboard shortcuts
│   ├── sidebar.py       # Collapsible sidebar: history list, search, theme toggle
│   └── assessment_panel.py  # Input fields, dropdowns, result display
├── core/
│   ├── llm.py           # LLM interaction via langchain-ollama (cached ChatOllama)
│   ├── history_store.py # Observable in-memory history list
│   ├── persistence.py   # SQLite-backed history persistence
│   ├── model_fetcher.py # Ollama model discovery via the ollama Python client
│   └── paths.py         # platformdirs-based config/data directory resolution
├── services/
│   └── assessor.py      # Orchestrates assessment: runs LLM calls, updates UI, saves history
└── tests/               # pytest / pytest-asyncio, full mock coverage
```

## Key Components

### UI Layer (`ui/`)

- **`app.py`** — Flet `Page` setup. Dark theme by default (`ft.ThemeMode.DARK`). Registers keyboard shortcut (`Ctrl+Enter` to assess). Spawns a background thread to discover Ollama models.
- **`sidebar.py`** — `Sidebar` widget. Contains new-assessment and search buttons, a theme toggle (dark ↔ light), and a scrollable history list. Uses `platformdirs`-backed paths.
- **`assessment_panel.py`** — `AssessmentPanel` widget. Encapsulates the text input, language/formality/model dropdowns, assess button with loading indicator, and the results area (grammar verdict, feedback box, suggestion box).

### Core Layer (`core/`)

- **`llm.py`** — `get_llm(model)` returns a **cached** `ChatOllama` instance (singleton per model). `check_grammar(...)` sends a yes/no prompt; on `no`, it immediately calls `get_feedback_and_suggestion(...)` for detailed correction. Both are `async` and handle `ConnectError` from `httpx`.
- **`history_store.py`** — `HistoryStore` holds an in-memory list of `HistoryEntry` objects, supports change-notification callbacks, and delegates persistence to SQLite. Entries are prepended (newest first).
- **`persistence.py`** — SQLite table `history` keyed by `platformdirs` `user_data_dir`. Schema created on first connect.
- **`model_fetcher.py`** — Calls `ollama.list()` and returns sorted model names. Runs in a **background thread** (via `threading.Thread`) to avoid blocking the UI.
- **`paths.py`** — `HISTORY_DB = data_dir() / "history.db"` and `SETTINGS_JSON = config_dir() / "settings.json"`.

### Service Layer (`services/`)

- **`assessor.py`** — `AssessorService`. Manages the assess/cancel lifecycle. When assess is triggered, calls `check_grammar`; on result, updates the panel and persists the entry. Supports cancelling an in-flight request.

### Tests (`tests/`)

- Uses `pytest` + `pytest-asyncio`. `ChatOllama` is fully mocked.
- `test_main.py` — LLM logic, history store, persistence, model fetcher, sidebar search.
- `test_paths.py` — Platform dir mocking.
- `test_persistence.py` — SQLite with `tmp_path`.
- A `reset_llm_globals` fixture resets the module-level LLM cache before each test.

## UI / Theme

The app defaults to **dark mode** (`ft.ThemeMode.DARK`). The sidebar contains a toggle button (moon/sun icon) that switches between dark and light. Colour constants use Flet's `ft.Colors` semantic tokens throughout.

## Adding a Language or Formality

Dropdown options in `assessment_panel.py` are defined statically in the constructor. Adding a new language or formality level is a two-step edit in `AssessmentPanel.__init__`.

## Ollama Compatibility

Requires a running local Ollama instance with at least one pulled model (e.g. `ollama pull llama3.2`). The model-fetching thread runs on startup; if Ollama is unavailable, the dropdown remains empty and a status message is shown.
