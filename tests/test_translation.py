"""Tests for Translation mode — parser and translate_text LLM function.

Covers:
  - _parse_translations (full, short, malformed, continuation lines, missing
    indices, missing tags, blank input)
  - translate_text (mocked LLM: full response, empty input short-circuit,
    ConnectError sentinel, generic Exception sentinel)
"""

from unittest.mock import AsyncMock, patch

import pytest
from httpx import ConnectError

from core.llm import _parse_translations, translate_text


# ---------------------------------------------------------------------------
# Parser tests
# ---------------------------------------------------------------------------


class TestParseTranslations:
    def test_full_response(self):
        content = (
            "1. TRANSLATION: Hello there.\n"
            "   TAG: formal\n"
            "2. TRANSLATION: Hi.\n"
            "   TAG: casual\n"
            "3. TRANSLATION: Hey, how's it going?\n"
            "   TAG: idiomatic\n"
        )
        out = _parse_translations(content, expected_count=3)
        assert out == [
            ("Hello there.", "formal"),
            ("Hi.", "casual"),
            ("Hey, how's it going?", "idiomatic"),
        ]

    def test_short_response_returns_what_was_parsed(self):
        content = (
            "1. TRANSLATION: Hello\n"
            "   TAG: formal\n"
        )
        out = _parse_translations(content, expected_count=5)
        assert out == [("Hello", "formal")]

    def test_skips_missing_indices(self):
        content = (
            "1. TRANSLATION: Hello\n"
            "   TAG: formal\n"
            "3. TRANSLATION: Hey\n"
            "   TAG: casual\n"
        )
        out = _parse_translations(content, expected_count=3)
        # Index 2 is missing — only return what we got, in order.
        assert out == [
            ("Hello", "formal"),
            ("Hey", "casual"),
        ]

    def test_missing_tag_defaults_to_empty(self):
        content = (
            "1. TRANSLATION: Hello\n"
            "2. TRANSLATION: Hi\n"
        )
        out = _parse_translations(content, expected_count=2)
        assert out == [("Hello", ""), ("Hi", "")]

    def test_skips_entries_with_empty_translation(self):
        content = (
            "1. TRANSLATION:\n"
            "   TAG: formal\n"
            "2. TRANSLATION: Hi\n"
        )
        out = _parse_translations(content, expected_count=2)
        assert out == [("Hi", "")]

    def test_handles_unnumbered_continuation_line(self):
        # A bare "TAG: <text>" on its own line (no leading "1.") should
        # attach to the most recent (index, field) — here, tag for #1.
        content = (
            "1. TRANSLATION: Hello\n"
            "TAG: formal\n"
            "2. TRANSLATION: Hi\n"
            "   TAG: casual\n"
        )
        out = _parse_translations(content, expected_count=2)
        assert out == [("Hello", "formal"), ("Hi", "casual")]

    def test_handles_multiline_translation_via_continuation(self):
        content = (
            "1. TRANSLATION: Hello there,\n"
            "   my friend.\n"
            "   TAG: formal\n"
            "2. TRANSLATION: Hi.\n"
            "   TAG: casual\n"
        )
        out = _parse_translations(content, expected_count=2)
        assert out == [
            ("Hello there,\nmy friend.", "formal"),
            ("Hi.", "casual"),
        ]

    def test_handles_field_without_leading_space(self):
        # Model may emit "1.TRANSLATION:" without a space after the period.
        content = (
            "1.TRANSLATION: Hello\n"
            "   TAG: formal\n"
        )
        out = _parse_translations(content, expected_count=1)
        assert out == [("Hello", "formal")]

    def test_malformed_response_returns_empty(self):
        assert _parse_translations("no structure here", expected_count=5) == []
        assert _parse_translations("", expected_count=5) == []

    def test_ignores_blank_lines(self):
        content = (
            "\n"
            "1. TRANSLATION: Hello\n"
            "   TAG: formal\n"
            "\n"
            "2. TRANSLATION: Hi\n"
            "   TAG: casual\n"
            "\n"
        )
        out = _parse_translations(content, expected_count=2)
        assert out == [("Hello", "formal"), ("Hi", "casual")]

    def test_case_insensitive_field_names(self):
        content = (
            "1. translation: Hello\n"
            "   tag: formal\n"
            "2. Translation: Hi\n"
            "   Tag: casual\n"
        )
        out = _parse_translations(content, expected_count=2)
        assert out == [("Hello", "formal"), ("Hi", "casual")]


# ---------------------------------------------------------------------------
# translate_text tests (mocked LLM)
# ---------------------------------------------------------------------------


class TestTranslateText:
    @pytest.mark.asyncio
    async def test_returns_parsed_variants(self):
        mock_llm = AsyncMock()
        mock_llm.ainvoke = AsyncMock(
            return_value=AsyncMock(
                content=(
                    "1. TRANSLATION: Hello.\n"
                    "   TAG: formal\n"
                    "2. TRANSLATION: Hi.\n"
                    "   TAG: casual\n"
                )
            )
        )
        with patch("core.llm.get_llm", return_value=mock_llm):
            out = await translate_text(
                text="Zdravo",
                source_language="Serbian",
                target_language="English",
                formality="Colloquial",
                count=2,
                model="test-model",
            )
        assert out == [("Hello.", "formal"), ("Hi.", "casual")]

    @pytest.mark.asyncio
    async def test_empty_text_returns_empty(self):
        out = await translate_text(
            text="",
            source_language="Auto-detect",
            target_language="English",
            formality="Colloquial",
            count=3,
            model="test-model",
        )
        assert out == []

    @pytest.mark.asyncio
    async def test_blank_text_returns_empty(self):
        out = await translate_text(
            text="   \n  ",
            source_language="Auto-detect",
            target_language="English",
            formality="Colloquial",
            count=3,
            model="test-model",
        )
        assert out == []

    @pytest.mark.asyncio
    async def test_zero_count_returns_empty(self):
        out = await translate_text(
            text="Hello",
            source_language="Auto-detect",
            target_language="French",
            formality="Colloquial",
            count=0,
            model="test-model",
        )
        assert out == []

    @pytest.mark.asyncio
    async def test_missing_target_language_returns_empty(self):
        out = await translate_text(
            text="Hello",
            source_language="Auto-detect",
            target_language="",
            formality="Colloquial",
            count=3,
            model="test-model",
        )
        assert out == []

    @pytest.mark.asyncio
    async def test_connect_error_returns_sentinel(self):
        mock_llm = AsyncMock()
        mock_llm.ainvoke = AsyncMock(side_effect=ConnectError("refused"))
        with patch("core.llm.get_llm", return_value=mock_llm):
            out = await translate_text(
                text="Hello",
                source_language="Auto-detect",
                target_language="French",
                formality="Colloquial",
                count=3,
                model="test-model",
            )
        assert out == [("Cannot connect to Ollama.", "error")]

    @pytest.mark.asyncio
    async def test_generic_exception_returns_sentinel(self):
        mock_llm = AsyncMock()
        mock_llm.ainvoke = AsyncMock(side_effect=RuntimeError("boom"))
        with patch("core.llm.get_llm", return_value=mock_llm):
            out = await translate_text(
                text="Hello",
                source_language="Auto-detect",
                target_language="French",
                formality="Colloquial",
                count=3,
                model="test-model",
            )
        assert out == [("Error: boom", "error")]

    @pytest.mark.asyncio
    async def test_unparseable_response_falls_back_to_raw_content(self):
        mock_llm = AsyncMock()
        mock_llm.ainvoke = AsyncMock(
            return_value=AsyncMock(content="Some freeform response without structure.")
        )
        with patch("core.llm.get_llm", return_value=mock_llm):
            out = await translate_text(
                text="Hello",
                source_language="Auto-detect",
                target_language="French",
                formality="Colloquial",
                count=3,
                model="test-model",
            )
        # When parsing yields nothing, translate_text returns the raw content
        # so the user can still see the model's reply.
        assert out == [("Some freeform response without structure.", "")]

    @pytest.mark.asyncio
    async def test_auto_detect_passes_through(self):
        # Source "Auto-detect" is allowed and should not raise.
        mock_llm = AsyncMock()
        mock_llm.ainvoke = AsyncMock(
            return_value=AsyncMock(
                content="1. TRANSLATION: Bonjour.\n   TAG: formal\n"
            )
        )
        with patch("core.llm.get_llm", return_value=mock_llm):
            out = await translate_text(
                text="Hello",
                source_language="Auto-detect",
                target_language="French",
                formality="Colloquial",
                count=1,
                model="test-model",
            )
        assert out == [("Bonjour.", "formal")]
