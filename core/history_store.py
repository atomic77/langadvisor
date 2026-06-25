"""In-memory history storage with change notifications."""

from dataclasses import dataclass, field
from typing import Callable


@dataclass
class HistoryEntry:
    text: str
    language: str
    formality: str
    model: str
    verdict: str
    feedback: str = ""
    suggestion: str = ""


class HistoryStore:
    """Observable in-memory list of assessment history entries backed by SQLite."""

    def __init__(self, persist: bool = True):
        self._entries: list[HistoryEntry] = []
        self._listeners: list[Callable] = []
        self._persist = persist
        if persist:
            from core.persistence import load_entries
            self._entries = load_entries()

    def add(self, entry: HistoryEntry) -> None:
        self._entries.insert(0, entry)
        if self._persist:
            from core.persistence import save_entry
            save_entry(entry)
        self._notify()

    def clear(self) -> None:
        self._entries.clear()
        if self._persist:
            from core.persistence import clear_entries
            clear_entries()
        self._notify()

    def get(self, idx: int) -> HistoryEntry:
        return self._entries[idx]

    def all(self) -> list[HistoryEntry]:
        return list(self._entries)

    def on_change(self, callback: Callable) -> None:
        self._listeners.append(callback)

    def _notify(self) -> None:
        for cb in self._listeners:
            cb()
