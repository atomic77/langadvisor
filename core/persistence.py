"""SQLite-backed persistence for assessment history and app settings."""

import json
import sqlite3
from pathlib import Path

from core.history_store import HistoryEntry
from core.languages import DEFAULT_ENABLED_LANGUAGES
from core.lesson_store import LessonEntry
from core.paths import HISTORY_DB


SCHEMA = """
CREATE TABLE IF NOT EXISTS history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    text TEXT NOT NULL,
    language TEXT,
    formality TEXT,
    model TEXT,
    verdict TEXT,
    feedback TEXT,
    suggestion TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT
);

CREATE TABLE IF NOT EXISTS lesson_rounds (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    language TEXT,
    formality TEXT,
    ects_level TEXT,
    category TEXT,
    model TEXT,
    phrases_json TEXT,
    answers_json TEXT,
    results_json TEXT,
    summary TEXT,
    score_total INTEGER,
    score_max INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""


def _ensure_db(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        conn.executescript(SCHEMA)


def load_entries(db_path: Path | None = None) -> list[HistoryEntry]:
    path = db_path or HISTORY_DB
    _ensure_db(path)
    with sqlite3.connect(path) as conn:
        cursor = conn.execute(
            "SELECT text, language, formality, model, verdict, feedback, suggestion "
            "FROM history ORDER BY id DESC"
        )
        rows = cursor.fetchall()
    return [
        HistoryEntry(
            text=r[0],
            language=r[1],
            formality=r[2],
            model=r[3],
            verdict=r[4],
            feedback=r[5] or "",
            suggestion=r[6] or "",
        )
        for r in rows
    ]


def save_entry(entry: HistoryEntry, db_path: Path | None = None) -> None:
    path = db_path or HISTORY_DB
    _ensure_db(path)
    with sqlite3.connect(path) as conn:
        conn.execute(
            "INSERT INTO history (text, language, formality, model, verdict, feedback, suggestion) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                entry.text,
                entry.language,
                entry.formality,
                entry.model,
                entry.verdict,
                entry.feedback,
                entry.suggestion,
            ),
        )
        conn.commit()


def clear_entries(db_path: Path | None = None) -> None:
    """Remove all persisted assessment history entries."""
    path = db_path or HISTORY_DB
    _ensure_db(path)
    with sqlite3.connect(path) as conn:
        conn.execute("DELETE FROM history")
        conn.commit()


def load_setting(key: str, db_path: Path | None = None) -> str | None:
    """Load a setting value by key from SQLite."""
    path = db_path or HISTORY_DB
    _ensure_db(path)
    with sqlite3.connect(path) as conn:
        cursor = conn.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = cursor.fetchone()
    return row[0] if row else None


def save_setting(key: str, value: str, db_path: Path | None = None) -> None:
    """Persist a setting key/value to SQLite."""
    path = db_path or HISTORY_DB
    _ensure_db(path)
    with sqlite3.connect(path) as conn:
        conn.execute(
            "INSERT INTO settings (key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, value),
        )
        conn.commit()


DEFAULT_MODEL_KEY = "default_model"
ENABLED_LANGUAGES_KEY = "enabled_languages"
UI_FONT_SCALE_KEY = "ui_font_scale"
UI_FONT_FAMILY_KEY = "ui_font_family"


def load_default_model(db_path: Path | None = None) -> str | None:
    """Load the app default model, if one has been persisted."""
    return load_setting(DEFAULT_MODEL_KEY, db_path=db_path)


def save_default_model(model: str, db_path: Path | None = None) -> None:
    """Persist the app default model."""
    save_setting(DEFAULT_MODEL_KEY, model, db_path=db_path)


def load_enabled_languages(db_path: Path | None = None) -> list[str]:
    """Load selected languages; fall back to the app's original defaults."""
    value = load_setting(ENABLED_LANGUAGES_KEY, db_path=db_path)
    if not value:
        return DEFAULT_ENABLED_LANGUAGES.copy()

    try:
        loaded = json.loads(value)
    except json.JSONDecodeError:
        return DEFAULT_ENABLED_LANGUAGES.copy()

    if not isinstance(loaded, list):
        return DEFAULT_ENABLED_LANGUAGES.copy()

    return [str(item) for item in loaded if str(item).strip()]


def save_enabled_languages(languages: list[str], db_path: Path | None = None) -> None:
    """Persist selected languages as JSON."""
    save_setting(ENABLED_LANGUAGES_KEY, json.dumps(languages), db_path=db_path)

def load_ui_font_scale(db_path: Path | None = None) -> float:
    """Load persisted UI font scale with validation and fallback."""
    value = load_setting(UI_FONT_SCALE_KEY, db_path=db_path)
    if value is None:
        return 1.0
    try:
        scale = float(value)
    except (TypeError, ValueError):
        return 1.0
    if 0.9 <= scale <= 1.6:
        return scale
    return 1.0


def save_ui_font_scale(scale: float, db_path: Path | None = None) -> None:
    """Persist UI font scale."""
    save_setting(UI_FONT_SCALE_KEY, f"{float(scale):.3f}", db_path=db_path)


def load_ui_font_family(db_path: Path | None = None) -> str:
    """Load persisted UI font family token."""
    value = load_setting(UI_FONT_FAMILY_KEY, db_path=db_path)
    return value or ""


def save_ui_font_family(font_family: str, db_path: Path | None = None) -> None:
    """Persist UI font family token."""
    save_setting(UI_FONT_FAMILY_KEY, font_family or "", db_path=db_path)



# ---------------------------------------------------------------------------
# Lesson rounds
# ---------------------------------------------------------------------------


def load_lesson_rounds(db_path: Path | None = None) -> list[LessonEntry]:
    """Load all persisted lesson rounds, newest first."""
    path = db_path or HISTORY_DB
    _ensure_db(path)
    with sqlite3.connect(path) as conn:
        cursor = conn.execute(
            "SELECT language, formality, ects_level, category, model, "
            "phrases_json, answers_json, results_json, summary, score_total, score_max "
            "FROM lesson_rounds ORDER BY id DESC"
        )
        rows = cursor.fetchall()
    entries: list[LessonEntry] = []
    for r in rows:
        try:
            phrases = [tuple(p) for p in json.loads(r[5] or "[]")]
        except (json.JSONDecodeError, TypeError, ValueError):
            phrases = []
        try:
            answers = list(json.loads(r[6] or "[]"))
        except (json.JSONDecodeError, TypeError, ValueError):
            answers = []
        try:
            results = list(json.loads(r[7] or "[]"))
        except (json.JSONDecodeError, TypeError, ValueError):
            results = []
        entries.append(
            LessonEntry(
                language=r[0] or "",
                formality=r[1] or "",
                ects_level=r[2] or "",
                category=r[3] or "",
                model=r[4] or "",
                phrases=phrases,
                answers=[str(a) for a in answers],
                results=results,
                summary=r[8] or "",
                score_total=int(r[9] or 0),
                score_max=int(r[10] or 0),
            )
        )
    return entries


def save_lesson_round(entry: LessonEntry, db_path: Path | None = None) -> None:
    """Persist a completed lesson round."""
    path = db_path or HISTORY_DB
    _ensure_db(path)
    with sqlite3.connect(path) as conn:
        conn.execute(
            "INSERT INTO lesson_rounds (language, formality, ects_level, category, model, "
            "phrases_json, answers_json, results_json, summary, score_total, score_max) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                entry.language,
                entry.formality,
                entry.ects_level,
                entry.category,
                entry.model,
                json.dumps([list(p) for p in entry.phrases]),
                json.dumps(entry.answers),
                json.dumps(entry.results),
                entry.summary,
                entry.score_total,
                entry.score_max,
            ),
        )
        conn.commit()


def clear_lesson_rounds(db_path: Path | None = None) -> None:
    """Remove all persisted lesson rounds."""
    path = db_path or HISTORY_DB
    _ensure_db(path)
    with sqlite3.connect(path) as conn:
        conn.execute("DELETE FROM lesson_rounds")
        conn.commit()
