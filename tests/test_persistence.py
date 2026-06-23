"""Tests for SQLite persistence layer."""

from pathlib import Path

import pytest

from core.history_store import HistoryEntry
from core.persistence import load_entries, save_entry


@pytest.fixture
def temp_db(tmp_path):
    return tmp_path / "test_history.db"


class TestPersistence:
    def test_load_empty_db(self, temp_db):
        entries = load_entries(temp_db)
        assert entries == []

    def test_save_and_load(self, temp_db):
        entry = HistoryEntry(
            text="Bonjour",
            language="French",
            formality="Formal",
            model="mistral",
            verdict="yes",
        )
        save_entry(entry, temp_db)
        entries = load_entries(temp_db)
        assert len(entries) == 1
        assert entries[0].text == "Bonjour"
        assert entries[0].language == "French"
        assert entries[0].verdict == "yes"

    def test_load_order_is_newest_first(self, temp_db):
        e1 = HistoryEntry(text="First", language="L", formality="F", model="m", verdict="yes")
        e2 = HistoryEntry(text="Second", language="L", formality="F", model="m", verdict="no", feedback="bad")
        save_entry(e1, temp_db)
        save_entry(e2, temp_db)
        entries = load_entries(temp_db)
        assert [e.text for e in entries] == ["Second", "First"]

    def test_null_feedback_defaults_to_empty(self, temp_db):
        entry = HistoryEntry(text="Hi", language="E", formality="C", model="m", verdict="yes")
        save_entry(entry, temp_db)
        entries = load_entries(temp_db)
        assert entries[0].feedback == ""
        assert entries[0].suggestion == ""
