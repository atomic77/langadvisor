"""Tests for SQLite persistence layer."""

import pytest

from core.history_store import HistoryEntry
from core.languages import DEFAULT_ENABLED_LANGUAGES
from core.persistence import (
    load_default_model,
    load_enabled_languages,
    load_entries,
    load_setting,
    save_default_model,
    save_enabled_languages,
    save_entry,
    save_setting,
)


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
        e1 = HistoryEntry(
            text="First", language="L", formality="F", model="m", verdict="yes"
        )
        e2 = HistoryEntry(
            text="Second",
            language="L",
            formality="F",
            model="m",
            verdict="no",
            feedback="bad",
        )
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

    def test_save_and_load_generic_setting(self, temp_db):
        save_setting("theme", "dark", temp_db)
        assert load_setting("theme", temp_db) == "dark"

    def test_save_setting_overwrites_previous_value(self, temp_db):
        save_setting("theme", "dark", temp_db)
        save_setting("theme", "light", temp_db)
        assert load_setting("theme", temp_db) == "light"

    def test_save_and_load_default_model(self, temp_db):
        save_default_model("llama3.2", temp_db)
        assert load_default_model(temp_db) == "llama3.2"

    def test_save_and_load_enabled_languages(self, temp_db):
        save_enabled_languages(["English", "Spanish", "Japanese"], temp_db)
        assert load_enabled_languages(temp_db) == ["English", "Spanish", "Japanese"]

    def test_enabled_languages_defaults_when_missing(self, temp_db):
        assert load_enabled_languages(temp_db) == DEFAULT_ENABLED_LANGUAGES

    def test_enabled_languages_defaults_when_corrupt(self, temp_db):
        save_setting("enabled_languages", "{not-json", temp_db)
        assert load_enabled_languages(temp_db) == DEFAULT_ENABLED_LANGUAGES
