"""Unit tests for the grammar assessor application.

Covers:
  - Core LLM logic (with mocked ChatOllama)
  - History store behaviour
  - Model fetcher
  - Sidebar search
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio

from core.history_store import HistoryEntry, HistoryStore
from core.llm import check_grammar, get_feedback_and_suggestion, get_llm, set_default_model
from core.model_fetcher import fetch_ollama_models
from ui.assessment_panel import AssessmentPanel
from ui.practice_panel import PracticePanel
from ui.sidebar import Sidebar


@pytest.fixture(autouse=True)
def reset_llm_globals():
    """Reset the module-level LLM cache before each test."""
    import core.llm as llm_mod
    llm_mod._llm = None
    llm_mod._current_model = None
    llm_mod._default_model = None


# ---------------------------------------------------------------------------
# get_llm
# ---------------------------------------------------------------------------

class TestGetLlm:
    @patch("core.llm.ChatOllama")
    def test_creates_instance(self, mock_cls):
        mock_inst = MagicMock()
        mock_cls.return_value = mock_inst
        llm = get_llm("mistral")
        mock_cls.assert_called_once_with(model="mistral", temperature=0)
        assert llm is mock_inst

    @patch("core.llm.ChatOllama")
    def test_returns_cached_instance(self, mock_cls):
        mock_inst = MagicMock()
        mock_cls.return_value = mock_inst
        first = get_llm("mistral")
        second = get_llm("mistral")
        mock_cls.assert_called_once()
        assert first is second

    @patch("core.llm.ChatOllama")
    def test_recreates_for_different_model(self, mock_cls):
        mock_cls.return_value = MagicMock()
        get_llm("mistral")
        get_llm("llama3")
        assert mock_cls.call_count == 2


# ---------------------------------------------------------------------------
# get_feedback_and_suggestion
# ---------------------------------------------------------------------------

class TestGetFeedbackAndSuggestion:
    @pytest.fixture
    def mock_llm(self):
        llm = MagicMock()
        llm.ainvoke = AsyncMock()
        return llm

    @patch("core.llm.get_llm")
    @pytest.mark.asyncio
    async def test_parses_feedback_and_suggestion(self, mock_get_llm, mock_llm):
        mock_get_llm.return_value = mock_llm
        mock_llm.ainvoke.return_value = MagicMock(
            content="FEEDBACK: Missing verb.\nSUGGESTION: Hello world."
        )
        fb, sug = await get_feedback_and_suggestion("hello world", "English", "Formal", "mistral")
        assert fb == "Missing verb."
        assert sug == "Hello world."

    @patch("core.llm.get_llm")
    @pytest.mark.asyncio
    async def test_fallback_to_full_content(self, mock_get_llm, mock_llm):
        mock_get_llm.return_value = mock_llm
        mock_llm.ainvoke.return_value = MagicMock(content="Some unexpected response")
        fb, sug = await get_feedback_and_suggestion("x", "English", "Formal", "mistral")
        assert fb == "Some unexpected response"
        assert sug == ""

    @patch("core.llm.get_llm")
    @pytest.mark.asyncio
    async def test_connect_error(self, mock_get_llm, mock_llm):
        from httpx import ConnectError
        mock_get_llm.return_value = mock_llm
        mock_llm.ainvoke.side_effect = ConnectError("nope")
        fb, sug = await get_feedback_and_suggestion("x", "English", "Formal", "mistral")
        assert "Cannot connect to Ollama" in fb
        assert sug == ""


# ---------------------------------------------------------------------------
# check_grammar
# ---------------------------------------------------------------------------

class TestCheckGrammar:
    @patch("core.llm.get_llm")
    @patch("core.llm.get_feedback_and_suggestion")
    @pytest.mark.asyncio
    async def test_verdict_yes_no_feedback(self, mock_fb, mock_get_llm):
        llm = MagicMock()
        llm.ainvoke = AsyncMock(return_value=MagicMock(content=" yes "))
        mock_get_llm.return_value = llm
        verdict, fb, sug = await check_grammar("Bonjour", "French", "Formal", "mistral")
        assert verdict == "yes"
        assert fb == ""
        assert sug == ""
        mock_fb.assert_not_awaited()

    @patch("core.llm.get_llm")
    @patch("core.llm.get_feedback_and_suggestion")
    @pytest.mark.asyncio
    async def test_verdict_no_fetches_feedback(self, mock_fb, mock_get_llm):
        llm = MagicMock()
        llm.ainvoke = AsyncMock(return_value=MagicMock(content="no"))
        mock_get_llm.return_value = llm
        mock_fb.return_value = ("Bad grammar.", "Corrected.")
        verdict, fb, sug = await check_grammar("Helo", "English", "Colloquial", "mistral")
        assert verdict == "no"
        assert fb == "Bad grammar."
        assert sug == "Corrected."
        mock_fb.assert_awaited_once()

    @patch("core.llm.get_llm")
    @pytest.mark.asyncio
    async def test_empty_text(self, mock_get_llm):
        verdict, fb, sug = await check_grammar("   ", "English", "Colloquial", "mistral")
        assert verdict == ""
        assert fb == ""
        assert sug == ""
        mock_get_llm.assert_not_called()

    @patch("core.llm.get_llm")
    @pytest.mark.asyncio
    async def test_unexpected_verdict_normalised(self, mock_get_llm):
        llm = MagicMock()
        llm.ainvoke = AsyncMock(return_value=MagicMock(content="maybe yes"))
        mock_get_llm.return_value = llm
        verdict, _, _ = await check_grammar("X", "English", "Colloquial", "mistral")
        assert verdict == "yes"


# ---------------------------------------------------------------------------
# HistoryStore
# ---------------------------------------------------------------------------

class TestHistoryStore:
    def test_add_notifies_listener(self):
        store = HistoryStore(persist=False)
        called = {"times": 0}

        def cb():
            called["times"] += 1

        store.on_change(cb)
        store.add(HistoryEntry(text="hi", language="English", formality="Formal", model="m", verdict="yes"))
        assert called["times"] == 1
        assert store.all()[0].text == "hi"

    def test_get_by_index(self):
        store = HistoryStore(persist=False)
        entry = HistoryEntry(text="a", language="L", formality="F", model="m", verdict="yes")
        store.add(entry)
        assert store.get(0) is entry

    @patch("core.persistence.load_entries")
    @patch("core.persistence.save_entry")
    def test_persist_loads_on_init(self, mock_save, mock_load):
        entry = HistoryEntry(text="saved", language="L", formality="F", model="m", verdict="yes")
        mock_load.return_value = [entry]
        store = HistoryStore(persist=True)
        assert store.all() == [entry]

    @patch("core.persistence.load_entries", return_value=[])
    @patch("core.persistence.save_entry")
    def test_persist_saves_on_add(self, mock_save, mock_load):
        store = HistoryStore(persist=True)
        entry = HistoryEntry(text="new", language="L", formality="F", model="m", verdict="no")
        store.add(entry)
        mock_save.assert_called_once_with(entry)

    def test_clear_removes_entries_and_notifies_listener(self):
        store = HistoryStore(persist=False)
        store.add(HistoryEntry(text="hi", language="English", formality="Formal", model="m", verdict="yes"))
        called = {"times": 0}

        def cb():
            called["times"] += 1

        store.on_change(cb)
        store.clear()

        assert store.all() == []
        assert called["times"] == 1

    @patch("core.persistence.load_entries", return_value=[])
    @patch("core.persistence.clear_entries")
    def test_persist_clears_entries(self, mock_clear, mock_load):
        store = HistoryStore(persist=True)
        store.clear()
        mock_clear.assert_called_once_with()


# ---------------------------------------------------------------------------
# Model fetcher
# ---------------------------------------------------------------------------

class TestModelFetcher:
    @patch("core.model_fetcher.ollama.list")
    def test_fetch_sorts_names(self, mock_list):
        m1 = MagicMock(model="z-model")
        m2 = MagicMock(model="a-model")
        mock_list.return_value = MagicMock(models=[m1, m2])
        names = fetch_ollama_models()
        assert names == ["a-model", "z-model"]


# ---------------------------------------------------------------------------
# Sidebar search
# ---------------------------------------------------------------------------

class TestSidebarSearch:
    @pytest.fixture
    def sample_store(self):
        store = HistoryStore(persist=False)
        store.add(HistoryEntry(text="Bonjour le monde", language="French", formality="Formal", model="m1", verdict="yes"))
        store.add(HistoryEntry(text="Helo world", language="English", formality="Colloquial", model="m2", verdict="no", feedback="Typo", suggestion="Hello world"))
        store.add(HistoryEntry(text="Ciao", language="Italian", formality="Business", model="m3", verdict="yes"))
        return store

    def test_matches_search_empty_query_matches_all(self, sample_store):
        sidebar = Sidebar(sample_store, on_new=lambda: None, on_load=lambda idx: None)
        for entry in sample_store.all():
            assert sidebar._matches_search(entry) is True

    def test_matches_search_by_text(self, sample_store):
        sidebar = Sidebar(sample_store, on_new=lambda: None, on_load=lambda idx: None)
        sidebar._search_query = "monde"
        results = [e for e in sample_store.all() if sidebar._matches_search(e)]
        assert len(results) == 1
        assert results[0].language == "French"

    def test_matches_search_by_language(self, sample_store):
        sidebar = Sidebar(sample_store, on_new=lambda: None, on_load=lambda idx: None)
        sidebar._search_query = "italian"
        results = [e for e in sample_store.all() if sidebar._matches_search(e)]
        assert len(results) == 1
        assert results[0].text == "Ciao"

    def test_matches_search_by_model(self, sample_store):
        sidebar = Sidebar(sample_store, on_new=lambda: None, on_load=lambda idx: None)
        sidebar._search_query = "m2"
        results = [e for e in sample_store.all() if sidebar._matches_search(e)]
        assert len(results) == 1
        assert results[0].text == "Helo world"

    def test_matches_search_by_feedback(self, sample_store):
        sidebar = Sidebar(sample_store, on_new=lambda: None, on_load=lambda idx: None)
        sidebar._search_query = "typo"
        results = [e for e in sample_store.all() if sidebar._matches_search(e)]
        assert len(results) == 1
        assert results[0].text == "Helo world"

    def test_matches_search_no_results(self, sample_store):
        sidebar = Sidebar(sample_store, on_new=lambda: None, on_load=lambda idx: None)
        sidebar._search_query = "zzzzz"
        results = [e for e in sample_store.all() if sidebar._matches_search(e)]
        assert len(results) == 0

    def test_clear_history_button_tracks_entries(self):
        store = HistoryStore(persist=False)
        sidebar = Sidebar(store, on_new=lambda: None, on_load=lambda idx: None)
        assert sidebar._clear_history_btn.disabled is True

        store.add(HistoryEntry(text="Hi", language="English", formality="Formal", model="m", verdict="yes"))
        assert sidebar._clear_history_btn.disabled is False

        store.clear()
        assert sidebar._clear_history_btn.disabled is True
        assert sidebar._history_list.controls == []


class TestLlmDefaultModel:
    @patch("core.llm.ChatOllama")
    def test_uses_default_model_when_input_model_empty(self, mock_cls):
        mock_cls.return_value = MagicMock()
        set_default_model("llama3")
        get_llm("")
        mock_cls.assert_called_once_with(model="llama3", temperature=0)

    def test_raises_when_no_model_available(self):
        with pytest.raises(ValueError):
            get_llm("")


class TestLanguageDropdownConfiguration:
    def test_assessment_panel_set_languages_keeps_existing_selection(self):
        panel = AssessmentPanel(on_assess_click=None, on_text_change=None, on_keyboard=None)
        panel.selected_language = "French"

        panel.set_languages(["English", "French", "German"])

        assert panel.selected_language == "French"
        assert [opt.key for opt in panel._lang_dropdown.options] == [
            "English",
            "French",
            "German",
        ]

    def test_assessment_panel_set_languages_falls_back_to_first(self):
        panel = AssessmentPanel(on_assess_click=None, on_text_change=None, on_keyboard=None)
        panel.selected_language = "Japanese"

        panel.set_languages(["English", "German"])

        assert panel.selected_language == "English"

    def test_practice_panel_set_languages_falls_back_to_first(self):
        panel = PracticePanel()
        panel._lang_dropdown.value = "Japanese"

        panel.set_languages(["Spanish", "Italian"])

        assert panel.selected_language == "Spanish"
        assert [opt.key for opt in panel._lang_dropdown.options] == ["Spanish", "Italian"]
