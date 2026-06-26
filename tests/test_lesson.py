"""Tests for Lesson mode — parsers, helpers, and LessonService.

Covers:
  - _parse_practice_set (full, short, malformed, continuation lines)
  - _parse_grade_batch (full, partial, malformed)
  - generate_practice_set / grade_practice_batch (mocked LLM)
  - LessonService state machine (start_round, next_step, prev_step, skip_step,
    submit_round, reset)
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core.lesson_store import LessonEntry, LessonStore
from core.llm import (
    _parse_grade_batch,
    _parse_phrase_translation,
    _parse_practice_set,
    generate_practice_set,
    grade_practice_batch,
)


# ---------------------------------------------------------------------------
# Parser tests
# ---------------------------------------------------------------------------


class TestParsePhraseTranslation:
    def test_parses_single_romanization_block(self):
        content = (
            "PHRASE: こんにちは\n"
            "TRANSLATION: Hello\n"
            "ROMANIZATION: konnichiwa"
        )
        assert _parse_phrase_translation(content, include_romanization=True) == (
            "こんにちは",
            "Hello",
            "konnichiwa",
        )


class TestParsePracticeSet:
    def test_full_response(self):
        content = (
            "1. PHRASE: Bonjour le monde\n   TRANSLATION: Hello the world\n"
            "2. PHRASE: Comment ça va\n   TRANSLATION: How are you\n"
            "3. PHRASE: Au revoir\n   TRANSLATION: Goodbye\n"
        )
        out = _parse_practice_set(content, expected_count=3)
        assert out == [
            ("Bonjour le monde", "Hello the world"),
            ("Comment ça va", "How are you"),
            ("Au revoir", "Goodbye"),
        ]

    def test_full_response_with_romanization(self):
        content = (
            "1. PHRASE: こんにちは\n   TRANSLATION: Hello\n"
            "   ROMANIZATION: konnichiwa\n"
            "2. PHRASE: ありがとう\n   TRANSLATION: Thank you\n"
            "   ROMANIZATION: arigatou\n"
        )
        out = _parse_practice_set(content, expected_count=2, include_romanization=True)
        assert out == [
            ("こんにちは", "Hello", "konnichiwa"),
            ("ありがとう", "Thank you", "arigatou"),
        ]

    def test_romanization_output_still_returns_two_fields_when_not_requested(self):
        content = (
            "1. PHRASE: こんにちは\n   TRANSLATION: Hello\n"
            "   ROMANIZATION: konnichiwa\n"
        )
        out = _parse_practice_set(content, expected_count=1)
        assert out == [("こんにちは", "Hello")]

    def test_short_response_returns_what_was_parsed(self):
        content = (
            "1. PHRASE: Hola\n   TRANSLATION: Hello\n"
            "2. PHRASE: Adiós\n   TRANSLATION: Goodbye\n"
        )
        out = _parse_practice_set(content, expected_count=10)
        assert len(out) == 2
        assert out[0] == ("Hola", "Hello")

    def test_skips_missing_indices(self):
        content = (
            "1. PHRASE: A\n   TRANSLATION: a-en\n"
            "3. PHRASE: C\n   TRANSLATION: c-en\n"
        )
        out = _parse_practice_set(content, expected_count=3)
        assert [p for p, _ in out] == ["A", "C"]

    def test_handles_field_without_leading_space(self):
        content = (
            "1.PHRASE: Hi\nTRANSLATION: Hello\n"
            "2.PHRASE: Bye\nTRANSLATION: Goodbye\n"
        )
        out = _parse_practice_set(content, expected_count=2)
        assert out == [("Hi", "Hello"), ("Bye", "Goodbye")]

    def test_skips_entries_with_empty_phrase(self):
        content = (
            "1. PHRASE: Hello\n   TRANSLATION: Hi\n"
            "2. PHRASE:\n   TRANSLATION: nothing\n"
        )
        out = _parse_practice_set(content, expected_count=2)
        assert len(out) == 1
        assert out[0] == ("Hello", "Hi")

    def test_malformed_response_returns_empty(self):
        assert _parse_practice_set("no structure here", expected_count=5) == []
        assert _parse_practice_set("", expected_count=5) == []


class TestParseGradeBatch:
    ITEMS = [
        ("Bonjour", "Hello", "Hello"),
        ("Au revoir", "bye", "Goodbye"),
    ]

    def test_full_response(self):
        content = (
            "1. SCORE: 10 | MISTAKES: None | BETTER: Hello\n"
            "2. SCORE: 6 | MISTAKES: Too informal | BETTER: Goodbye\n"
            "OVERALL: 16/20 | SUMMARY: Good effort overall.\n"
        )
        summary, results = _parse_grade_batch(content, self.ITEMS)
        assert summary == "Good effort overall."
        assert len(results) == 2
        assert results[0]["score"] == 10
        assert results[0]["better"] == "Hello"
        assert results[1]["score"] == 6
        assert results[1]["mistakes"] == "Too informal"

    def test_missing_indices_get_defaults(self):
        content = (
            "1. SCORE: 8 | MISTAKES: ok | BETTER: Hello\n"
        )
        _, results = _parse_grade_batch(content, self.ITEMS)
        assert len(results) == 2
        assert results[0]["score"] == 8
        assert results[1]["score"] == 0
        # Item 2 had a non-empty answer in ITEMS, so the fallback message
        # is "Not graded." rather than "Not answered.".
        assert results[1]["mistakes"] == "Not graded."
        assert results[1]["phrase"] == "Au revoir"

    def test_missing_index_with_empty_answer_says_not_answered(self):
        items = [("A", "x", "x"), ("B", "", "y")]
        content = "1. SCORE: 5 | MISTAKES: ok | BETTER: x\n"
        _, results = _parse_grade_batch(content, items)
        assert results[1]["mistakes"] == "Not answered."

    def test_missing_score_coerces_to_zero(self):
        content = (
            "1. SCORE: abc | MISTAKES: weird | BETTER: Hello\n"
            "2. SCORE: 15 | MISTAKES: too high | BETTER: Goodbye\n"
        )
        _, results = _parse_grade_batch(content, self.ITEMS)
        assert results[0]["score"] == 0
        # 15 clamps to 10.
        assert results[1]["score"] == 10

    def test_negative_score_clamps_to_zero(self):
        content = (
            "1. SCORE: -5 | MISTAKES: nope | BETTER: Hello\n"
            "2. SCORE: 7 | MISTAKES: ok | BETTER: Goodbye\n"
        )
        _, results = _parse_grade_batch(content, self.ITEMS)
        assert results[0]["score"] == 0
        assert results[1]["score"] == 7

    def test_no_overall_line_yields_empty_summary(self):
        content = (
            "1. SCORE: 5 | MISTAKES: x | BETTER: Hello\n"
            "2. SCORE: 5 | MISTAKES: y | BETTER: Goodbye\n"
        )
        summary, results = _parse_grade_batch(content, self.ITEMS)
        assert summary == ""
        assert len(results) == 2

    def test_empty_items_returns_empty(self):
        summary, results = _parse_grade_batch("anything", [])
        assert summary == ""
        assert results == []


# ---------------------------------------------------------------------------
# generate_practice_set / grade_practice_batch (mocked LLM)
# ---------------------------------------------------------------------------


class TestGeneratePracticeSet:
    @patch("core.llm.get_llm")
    @pytest.mark.asyncio
    async def test_returns_parsed_phrases(self, mock_get_llm):
        llm = MagicMock()
        llm.ainvoke = AsyncMock(
            return_value=MagicMock(
                content=(
                    "1. PHRASE: Bonjour\n   TRANSLATION: Hello\n"
                    "2. PHRASE: Salut\n   TRANSLATION: Hi\n"
                )
            )
        )
        mock_get_llm.return_value = llm
        out = await generate_practice_set(
            "French", "A1", "Colloquial", "Greetings", 2, "mistral"
        )
        assert out == [("Bonjour", "Hello"), ("Salut", "Hi")]

    @patch("core.llm.get_llm")
    @pytest.mark.asyncio
    async def test_returns_parsed_phrases_with_romanization(self, mock_get_llm):
        llm = MagicMock()
        llm.ainvoke = AsyncMock(
            return_value=MagicMock(
                content=(
                    "1. PHRASE: こんにちは\n   TRANSLATION: Hello\n"
                    "   ROMANIZATION: konnichiwa\n"
                )
            )
        )
        mock_get_llm.return_value = llm
        out = await generate_practice_set(
            "Japanese",
            "A1",
            "Colloquial",
            "Greetings",
            1,
            "mistral",
            include_romanization=True,
        )
        assert out == [("こんにちは", "Hello", "konnichiwa")]
        system_prompt = llm.ainvoke.await_args.args[0][0][1]
        assert "ROMANIZATION" in system_prompt
        assert "modified Hepburn" in system_prompt

    @patch("core.llm.get_llm")
    @pytest.mark.asyncio
    async def test_connect_error(self, mock_get_llm):
        from httpx import ConnectError

        llm = MagicMock()
        llm.ainvoke = AsyncMock(side_effect=ConnectError("nope"))
        mock_get_llm.return_value = llm
        out = await generate_practice_set(
            "French", "A1", "Colloquial", "Greetings", 3, "mistral"
        )
        assert out == [("Cannot connect to Ollama.", "")]

    @pytest.mark.asyncio
    async def test_invalid_args_returns_empty(self):
        out = await generate_practice_set(
            "", "A1", "Colloquial", "Greetings", 5, "mistral"
        )
        assert out == []


class TestGradePracticeBatch:
    @patch("core.llm.get_llm")
    @pytest.mark.asyncio
    async def test_returns_summary_and_results(self, mock_get_llm):
        llm = MagicMock()
        llm.ainvoke = AsyncMock(
            return_value=MagicMock(
                content=(
                    "1. SCORE: 9 | MISTAKES: none | BETTER: Hello\n"
                    "2. SCORE: 7 | MISTAKES: minor | BETTER: Goodbye\n"
                    "OVERALL: 16/20 | SUMMARY: Strong round."
                )
            )
        )
        mock_get_llm.return_value = llm
        items = [("Bonjour", "Hello", "Hello"), ("Au revoir", "bye", "Goodbye")]
        summary, results = await grade_practice_batch(
            items, "French", "Colloquial", "A1", "mistral"
        )
        assert summary == "Strong round."
        assert len(results) == 2
        assert results[0]["score"] == 9
        assert results[1]["score"] == 7

    @pytest.mark.asyncio
    async def test_empty_items_returns_empty(self):
        summary, results = await grade_practice_batch(
            [], "French", "Colloquial", "A1", "mistral"
        )
        assert summary == ""
        assert results == []


# ---------------------------------------------------------------------------
# LessonService state machine (smoke tests with mocked panel + page)
# ---------------------------------------------------------------------------


def _make_panel():
    """Build a real LessonPanel (cheap to construct; no Flet page required)."""
    from ui.lesson_panel import LessonPanel
    return LessonPanel()


class TestLessonPanelState:
    def test_practicing_reenables_submit_after_reviewing(self):
        panel = _make_panel()

        panel.show_practicing(0, 1, "A")
        assert panel._submit_btn.visible is True
        assert panel._submit_btn.disabled is False

        panel.show_reviewing()
        assert panel._submit_btn.disabled is True

        panel.show_practicing(0, 1, "B")
        assert panel._submit_btn.visible is True
        assert panel._submit_btn.disabled is False

    def test_practicing_shows_romanization_when_present(self):
        panel = _make_panel()

        panel.show_practicing(0, 1, "こんにちは", romanization="konnichiwa")

        assert panel._romanization_card.visible is True
        assert panel._romanization_text.value == "konnichiwa"

    def test_practicing_hides_romanization_when_missing(self):
        panel = _make_panel()

        panel.show_practicing(0, 1, "Bonjour", romanization="")

        assert panel._romanization_card.visible is False

    def test_practicing_reveals_cached_reference_translation(self):
        panel = _make_panel()

        panel.show_practicing(0, 1, "Bonjour", reference_translation="Hello")
        assert panel._reference_card.visible is False
        assert panel._reference_text.value == ""
        assert panel._help_btn.disabled is False

        panel.show_reference_translation()

        assert panel._reference_card.visible is True
        assert panel._reference_text.value == "Hello"

    def test_practicing_resets_reference_translation_between_steps(self):
        panel = _make_panel()

        panel.show_practicing(0, 2, "Bonjour", reference_translation="Hello")
        panel.show_reference_translation()
        panel.show_practicing(1, 2, "Merci", reference_translation="Thanks")

        assert panel._reference_card.visible is False
        assert panel._reference_text.value == ""
        assert panel._reference_translation == "Thanks"

    def test_practicing_disables_help_without_reference_translation(self):
        panel = _make_panel()

        panel.show_practicing(0, 1, "Bonjour", reference_translation="")

        assert panel._help_btn.disabled is True


class TestLessonServiceStartRound:
    @patch("core.llm.get_llm")
    @pytest.mark.asyncio
    async def test_populates_phrases_and_answers(self, mock_get_llm):
        llm = MagicMock()
        llm.ainvoke = AsyncMock(
            return_value=MagicMock(
                content=(
                    "1. PHRASE: A\n   TRANSLATION: a\n"
                    "2. PHRASE: B\n   TRANSLATION: b\n"
                    "3. PHRASE: C\n   TRANSLATION: c\n"
                )
            )
        )
        mock_get_llm.return_value = llm

        from services.lesson_service import LessonService

        panel = _make_panel()
        panel._round_size_dropdown.value = "3"
        page = MagicMock()
        store = LessonStore(persist=False)
        service = LessonService(panel, page, store)

        await service.on_start(None)

        assert service.state == "practicing"
        assert len(service._phrases) == 3
        assert service._answers == ["", "", ""]
        assert service._current == 0

    @patch("core.llm.get_llm")
    @pytest.mark.asyncio
    async def test_populates_romanization_when_enabled(self, mock_get_llm):
        llm = MagicMock()
        llm.ainvoke = AsyncMock(
            return_value=MagicMock(
                content=(
                    "1. PHRASE: こんにちは\n   TRANSLATION: Hello\n"
                    "   ROMANIZATION: konnichiwa\n"
                )
            )
        )
        mock_get_llm.return_value = llm

        from services.lesson_service import LessonService

        panel = _make_panel()
        panel._round_size_dropdown.value = "1"
        panel._latinization_checkbox.value = True
        page = MagicMock()
        store = LessonStore(persist=False)
        service = LessonService(panel, page, store)

        await service.on_start(None)

        assert service.state == "practicing"
        assert service._phrases == [("こんにちは", "Hello", "konnichiwa")]
        assert panel._romanization_card.visible is True
        assert panel._romanization_text.value == "konnichiwa"


class TestLessonServiceNavigation:
    def _service_with_three(self):
        from services.lesson_service import LessonService

        panel = _make_panel()
        page = MagicMock()
        store = LessonStore(persist=False)
        service = LessonService(panel, page, store)
        service._phrases = [("A", "a"), ("B", "b"), ("C", "c")]
        service._answers = ["", "", ""]
        service._current = 0
        service._state = "practicing"
        return service

    def test_next_advances_and_captures_answer(self):
        service = self._service_with_three()
        panel = service._panel
        panel._answer_input.value = "my A"
        service.on_next(None)
        assert service._current == 1
        assert service._answers[0] == "my A"

    def test_help_reveals_current_reference_without_changing_answer(self):
        service = self._service_with_three()
        panel = service._panel
        panel._answer_input.value = "draft answer"

        service.on_help(None)

        assert panel._reference_card.visible is True
        assert panel._reference_text.value == "a"
        assert service._answers == ["", "", ""]
        assert panel._answer_input.value == "draft answer"

    def test_next_at_end_is_noop(self):
        service = self._service_with_three()
        service._current = 2
        service.on_next(None)
        assert service._current == 2

    def test_prev_moves_back(self):
        service = self._service_with_three()
        service._current = 2
        service.on_prev(None)
        assert service._current == 1

    def test_skip_records_empty_and_advances(self):
        service = self._service_with_three()
        panel = service._panel
        panel._answer_input.value = "draft"
        service.on_skip(None)
        assert service._current == 1
        assert service._answers[0] == ""

    def test_reset_clears_state(self):
        service = self._service_with_three()
        service._last_summary = "blah"
        service.on_reset(None)
        assert service.state == "setup"
        assert service._phrases == []
        assert service._answers == []


class TestLessonStore:
    def test_add_and_get(self):
        store = LessonStore(persist=False)
        entry = LessonEntry(
            language="English", formality="Formal", ects_level="A1",
            category="Travel", model="m", phrases=[("hi", "hello")],
            answers=["hello"], results=[{"score": 10}],
            summary="great", score_total=10, score_max=10,
        )
        store.add(entry)
        assert store.get(0) is entry

    def test_clear_notifies(self):
        store = LessonStore(persist=False)
        store.add(LessonEntry(language="L", formality="F", ects_level="A1",
                              category="C", model="m"))
        called = {"n": 0}
        store.on_change(lambda: called.__setitem__("n", called["n"] + 1))
        store.clear()
        assert called["n"] == 1
        assert store.all() == []