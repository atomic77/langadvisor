"""Tests for SQLite persistence layer."""

import pytest

from core.history_store import HistoryEntry
from core.lesson_store import LessonEntry
from core.languages import DEFAULT_ENABLED_LANGUAGES
from core.persistence import (
    clear_entries,
    load_enabled_languages,
    load_entries,
    load_lesson_rounds,
    load_setting,
    load_ui_font_family,
    load_ui_font_scale,
    save_enabled_languages,
    save_entry,
    save_lesson_round,
    save_setting,
    save_ui_font_scale,
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

    def test_clear_entries_removes_history_only(self, temp_db):
        save_entry(
            HistoryEntry(text="Hi", language="E", formality="C", model="m", verdict="yes"),
            temp_db,
        )
        save_setting("theme", "dark", temp_db)

        clear_entries(temp_db)

        assert load_entries(temp_db) == []
        assert load_setting("theme", temp_db) == "dark"

    def test_save_and_load_generic_setting(self, temp_db):
        save_setting("theme", "dark", temp_db)
        assert load_setting("theme", temp_db) == "dark"

    def test_save_setting_overwrites_previous_value(self, temp_db):
        save_setting("theme", "dark", temp_db)
        save_setting("theme", "light", temp_db)
        assert load_setting("theme", temp_db) == "light"

    def test_save_and_load_enabled_languages(self, temp_db):
        save_enabled_languages(["English", "Spanish", "Japanese"], temp_db)
        assert load_enabled_languages(temp_db) == ["English", "Spanish", "Japanese"]

    @pytest.mark.parametrize(
        "raw_value",
        [None, "{not-json"],
        ids=["missing", "corrupt"],
    )
    def test_enabled_languages_defaults_when_missing_or_corrupt(self, temp_db, raw_value):
        if raw_value is not None:
            save_setting("enabled_languages", raw_value, temp_db)
        assert load_enabled_languages(temp_db) == DEFAULT_ENABLED_LANGUAGES

    def test_save_and_load_ui_font_scale(self, temp_db):
        save_ui_font_scale(1.25, temp_db)
        assert load_ui_font_scale(temp_db) == 1.25

    @pytest.mark.parametrize(
        "raw_value",
        [None, "abc", "3.0"],
        ids=["missing", "invalid", "out-of-bounds"],
    )
    def test_ui_font_scale_defaults_when_missing_invalid_or_oob(self, temp_db, raw_value):
        if raw_value is not None:
            save_setting("ui_font_scale", raw_value, temp_db)
        assert load_ui_font_scale(temp_db) == 1.0

    def test_ui_font_family_defaults_when_missing(self, temp_db):
        assert load_ui_font_family(temp_db) == ""

    def test_save_and_load_lesson_round_with_romanization(self, temp_db):
        entry = LessonEntry(
            language="Japanese",
            formality="Colloquial",
            ects_level="A1",
            category="Greetings",
            model="mistral",
            phrases=[("こんにちは", "Hello", "konnichiwa")],
            answers=["Hello"],
            results=[{"score": 10, "romanization": "konnichiwa"}],
            summary="Strong round.",
            score_total=10,
            score_max=10,
        )

        save_lesson_round(entry, temp_db)
        entries = load_lesson_rounds(temp_db)

        assert len(entries) == 1
        assert entries[0].phrases == [("こんにちは", "Hello", "konnichiwa")]
        assert entries[0].results[0]["romanization"] == "konnichiwa"

