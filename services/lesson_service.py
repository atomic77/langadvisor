"""Lesson service — orchestrates round generation, navigation, and batched grading."""

import asyncio

from core.lesson_store import LessonEntry, LessonStore
from core.llm import (
    generate_practice_sentence,
    generate_practice_set,
    get_default_model,
    grade_practice_batch,
)


def _phrase_text(phrase: tuple[str, ...]) -> str:
    return phrase[0] if len(phrase) > 0 else ""


def _phrase_reference(phrase: tuple[str, ...]) -> str:
    return phrase[1] if len(phrase) > 1 else ""


def _phrase_romanization(phrase: tuple[str, ...]) -> str:
    return phrase[2] if len(phrase) > 2 else ""


class LessonService:
    """Drives the LessonPanel state machine."""

    def __init__(self, panel, page, store: LessonStore):
        self._panel = panel
        self._page = page
        self._store = store

        self._phrases: list[tuple[str, ...]] = []   # (phrase, english, optional romanization)
        self._answers: list[str] = []
        self._current: int = 0
        self._state: str = "setup"
        self._last_results: list[dict] = []
        self._last_summary: str = ""
        self._running_task: asyncio.Task | None = None

    # -- public state --

    @property
    def state(self) -> str:
        return self._state

    # -- start / cancel generation --

    async def on_start(self, e) -> None:
        if self._running_task is not None and not self._running_task.done():
            self._running_task.cancel()
            self._running_task = None
            self._state = "setup"
            self._panel.show_setup()
            self._page.update()
            return

        count = self._panel.round_size
        self._state = "generating"
        self._panel.show_generating()
        self._page.update()

        language = self._panel.selected_language
        ects_level = self._panel.selected_ects_level
        formality = self._panel.selected_formality
        category = self._panel.selected_category
        model = get_default_model() or ""
        include_romanization = self._panel.latinization_enabled

        self._running_task = asyncio.current_task()
        try:
            phrases = await generate_practice_set(
                language,
                ects_level,
                formality,
                category,
                count,
                model,
                include_romanization=include_romanization,
            )
            # Pad with single-phrase retries if the batch came back short.
            attempts = 0
            while len(phrases) < count and attempts < 2:
                single_phrase = await generate_practice_sentence(
                    language,
                    ects_level,
                    formality,
                    category,
                    model,
                    include_romanization=include_romanization,
                )
                single = _phrase_text(single_phrase)
                if single and not single.lower().startswith(("error", "cannot")):
                    phrases.append(single_phrase)
                attempts += 1

            if not phrases:
                self._panel.set_status(
                    "Could not generate any phrases. Is Ollama running?",
                    is_error=True,
                )
                self._state = "setup"
                self._panel.show_setup()
                self._page.update()
                return

            self._phrases = phrases
            self._answers = ["" for _ in phrases]
            self._current = 0
            self._state = "practicing"
            if len(phrases) < count:
                self._panel.set_status(
                    f"Lesson has {len(phrases)} phrases (model returned fewer than {count}).",
                    is_error=False,
                )
            else:
                self._panel.set_status("")
            current_phrase = self._phrases[self._current]
            self._panel.show_practicing(
                self._current,
                len(self._phrases),
                _phrase_text(current_phrase),
                romanization=_phrase_romanization(current_phrase),
                reference_translation=_phrase_reference(current_phrase),
            )
            self._page.update()
        except asyncio.CancelledError:
            self._state = "setup"
            self._panel.show_setup()
            self._panel.set_status("Generation cancelled.")
            self._page.update()
        finally:
            self._running_task = None

    # -- navigation --

    def on_next(self, e) -> None:
        if self._state != "practicing" or not self._phrases:
            return
        # Capture current answer before advancing.
        self._answers[self._current] = self._panel.current_answer.strip()
        if self._current >= len(self._phrases) - 1:
            return  # last step — Submit Round handles it
        self._current += 1
        current_phrase = self._phrases[self._current]
        self._panel.show_practicing(
            self._current,
            len(self._phrases),
            _phrase_text(current_phrase),
            answer=self._answers[self._current],
            romanization=_phrase_romanization(current_phrase),
            reference_translation=_phrase_reference(current_phrase),
        )
        self._page.update()

    def on_prev(self, e) -> None:
        if self._state != "practicing" or not self._phrases:
            return
        # Persist any pending edit on the current step before navigating back.
        self._answers[self._current] = self._panel.current_answer.strip()
        if self._current <= 0:
            return
        self._current -= 1
        current_phrase = self._phrases[self._current]
        self._panel.show_practicing(
            self._current,
            len(self._phrases),
            _phrase_text(current_phrase),
            answer=self._answers[self._current],
            romanization=_phrase_romanization(current_phrase),
            reference_translation=_phrase_reference(current_phrase),
        )
        self._page.update()

    def on_help(self, e) -> None:
        if self._state != "practicing" or not self._phrases:
            return
        self._panel.show_reference_translation(
            _phrase_reference(self._phrases[self._current])
        )
        self._page.update()

    def on_skip(self, e) -> None:
        if self._state != "practicing" or not self._phrases:
            return
        self._answers[self._current] = ""
        if self._current >= len(self._phrases) - 1:
            return
        self._current += 1
        current_phrase = self._phrases[self._current]
        self._panel.show_practicing(
            self._current,
            len(self._phrases),
            _phrase_text(current_phrase),
            answer=self._answers[self._current],
            romanization=_phrase_romanization(current_phrase),
            reference_translation=_phrase_reference(current_phrase),
        )
        self._page.update()

    # -- submit & grade --

    async def on_submit(self, e) -> None:
        if self._state != "practicing" or not self._phrases:
            return
        if self._running_task is not None and not self._running_task.done():
            return  # already grading
        # Capture final answer.
        self._answers[self._current] = self._panel.current_answer.strip()

        self._state = "reviewing"
        self._panel.show_reviewing()
        self._page.update()

        model = get_default_model() or ""
        items = [
            (_phrase_text(phrase), self._answers[i] or "", _phrase_reference(phrase))
            for i, phrase in enumerate(self._phrases)
        ]

        self._running_task = asyncio.current_task()
        try:
            summary, results = await grade_practice_batch(
                items,
                self._panel.selected_language,
                self._panel.selected_formality,
                self._panel.selected_ects_level,
                model,
            )
            for result, phrase in zip(results, self._phrases):
                romanization = _phrase_romanization(phrase)
                if romanization:
                    result["romanization"] = romanization
            self._last_results = results
            self._last_summary = summary

            if not results:
                self._panel.set_status(
                    "Grading failed. Is Ollama running?", is_error=True
                )
                self._state = "setup"
                self._panel.show_setup()
                self._page.update()
                return

            score_total = sum(int(r.get("score", 0)) for r in results)
            score_max = 10 * len(results)

            self._state = "results"
            self._panel.show_results(results, summary, score_total, score_max)
            self._page.update()

            # Persist the round.
            self._store.add(
                LessonEntry(
                    language=self._panel.selected_language,
                    formality=self._panel.selected_formality,
                    ects_level=self._panel.selected_ects_level,
                    category=self._panel.selected_category,
                    model=model,
                    phrases=list(self._phrases),
                    answers=list(self._answers),
                    results=list(results),
                    summary=summary,
                    score_total=score_total,
                    score_max=score_max,
                )
            )
        except asyncio.CancelledError:
            self._state = "setup"
            self._panel.show_setup()
            self._panel.set_status("Grading cancelled.")
            self._page.update()
        finally:
            self._running_task = None

    # -- reset --

    def on_reset(self, e) -> None:
        if self._running_task is not None and not self._running_task.done():
            return
        self._phrases = []
        self._answers = []
        self._current = 0
        self._last_results = []
        self._last_summary = ""
        self._state = "setup"
        self._panel.show_setup()
        self._page.update()