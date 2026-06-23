"""SQLite-backed persistence for assessment history."""

import sqlite3
from pathlib import Path

from core.history_store import HistoryEntry
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
)
"""


def _ensure_db(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        conn.execute(SCHEMA)


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
            (entry.text, entry.language, entry.formality, entry.model, entry.verdict, entry.feedback, entry.suggestion),
        )
        conn.commit()
