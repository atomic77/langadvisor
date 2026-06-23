"""Practice service - generates phrases and checks user translations."""

import asyncio

from core.llm import check_translation, generate_practice_sentence


class PracticeService:
    """Handles phrase generation and translation checking."""

    def __init__(self, panel, page):
        self._panel = panel
        self._page = page
        self._running_task = None
        self._help_translation = ""

    async def on_generate(self, e) -> None:
        if self._running_task is not None and not self._running_task.done():
            self._running_task.cancel()
            self._running_task = None
            self._panel.set_generating(False)
            self._page.update()
            return

        self._panel.set_generating(True)
        self._panel.clear_output()
        self._help_translation = ""
        self._page.update()

        self._running_task = asyncio.current_task()
        try:
            phrase, translation = await generate_practice_sentence(
                self._panel.selected_language,
                self._panel.selected_ects_level,
                self._panel.selected_formality,
                self._panel.selected_category,
                self._panel.selected_model,
            )
            self._help_translation = translation
            self._panel.set_source_phrase(phrase)
            self._page.update()
        except asyncio.CancelledError:
            self._panel.set_source_phrase("(Generation cancelled)")
            self._page.update()
        finally:
            self._running_task = None
            self._panel.set_generating(False)
            self._page.update()

    async def on_check(self, e) -> None:
        if self._running_task is not None and not self._running_task.done():
            self._running_task.cancel()
            self._running_task = None
            self._panel.set_checking(False)
            self._page.update()
            return

        translation = self._panel.translation_text.strip()
        source = self._panel.source_phrase.strip()
        if not source:
            return
        if not translation:
            self._panel.show_error("Please enter your translation first.")
            self._page.update()
            return

        self._panel.set_checking(True)
        self._panel.clear_output()
        self._page.update()

        self._running_task = asyncio.current_task()
        try:
            mistakes = await check_translation(
                source,
                translation,
                self._panel.selected_language,
                self._panel.selected_formality,
                self._panel.selected_ects_level,
                self._panel.selected_model,
            )
            self._panel.show_mistakes(mistakes)
            self._page.update()
        except asyncio.CancelledError:
            self._page.update()
        finally:
            self._running_task = None
            self._panel.set_checking(False)
            self._page.update()

    async def on_help(self, e) -> None:
        if not self._panel.source_phrase.strip():
            return

        if self._help_translation:
            self._panel.show_help(self._help_translation)
        else:
            self._panel.show_error("Help is unavailable for this phrase.")
        self._page.update()
