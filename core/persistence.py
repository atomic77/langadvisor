"""SQLite-backed persistence for assessment history and app settings."""

import json
import sqlite3
from pathlib import Path

from core.history_store import HistoryEntry
from core.languages import DEFAULT_ENABLED_LANGUAGES
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
