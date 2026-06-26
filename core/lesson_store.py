"""In-memory storage for completed lesson rounds with change notifications."""

from dataclasses import dataclass, field
from typing import Callable


@dataclass
class LessonEntry:
    """A completed lesson round with phrases, user answers, and grading results."""
    language: str
    formality: str
    ects_level: str
    category: str
    model: str
    phrases: list[tuple[str, ...]] = field(default_factory=list)  # (phrase, english, optional romanization)
    answers: list[str] = field(default_factory=list)
    results: list[dict] = field(default_factory=list)              # per-item grading
    summary: str = ""
    score_total: int = 0
    score_max: int = 0


class LessonStore:
    """Observable in-memory list of completed lesson rounds backed by SQLite."""

    def __init__(self, persist: bool = True):
        self._entries: list[LessonEntry] = []
        self._listeners: list[Callable] = []
        self._persist = persist
        if persist:
            from core.persistence import load_lesson_rounds
            self._entries = load_lesson_rounds()

    def add(self, entry: LessonEntry) -> None:
        self._entries.insert(0, entry)
        if self._persist:
            from core.persistence import save_lesson_round
            save_lesson_round(entry)
        self._notify()

    def clear(self) -> None:
        self._entries.clear()
        if self._persist:
            from core.persistence import clear_lesson_rounds
            clear_lesson_rounds()
        self._notify()

    def get(self, idx: int) -> LessonEntry:
        return self._entries[idx]

    def all(self) -> list[LessonEntry]:
        return list(self._entries)

    def on_change(self, callback: Callable) -> None:
        self._listeners.append(callback)

    def _notify(self) -> None:
        for cb in self._listeners:
            cb()