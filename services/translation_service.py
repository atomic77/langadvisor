"""Translation service — coordinates LLM calls and UI updates for the Translation panel."""

import asyncio

from core.llm import get_default_model, translate_text


class TranslationService:
    """Handles running translations and updating the panel.

    Does not persist results to history (translation mode intentionally
    skips the sidebar history list).
    """

    def __init__(self, panel, page):
        self._panel = panel
        self._page = page
        self._running_task = None

    async def on_translate(self, e) -> None:
        if self._running_task is not None and not self._running_task.done():
            self._running_task.cancel()
            self._running_task = None
            self._panel.set_translating(False)
            self._panel.show_error("Translation cancelled.")
            self._page.update()
            return

        text = self._panel.input_text
        if not text.strip():
            return

        target = self._panel.selected_target_language
        if not target:
            self._panel.show_error("Please pick a target language.")
            self._page.update()
            return

        self._panel.set_translating(True)
        self._panel.clear_results()
        self._page.update()

        selected_model = self._panel.selected_model
        effective_model = selected_model or (get_default_model() or "")

        self._running_task = asyncio.current_task()
        try:
            variants = await translate_text(
                text,
                self._panel.selected_source_language,
                target,
                self._panel.selected_formality,
                self._panel.variation_count,
                selected_model,
            )
            # translate_text returns a single error sentinel for ConnectError/Exception.
            if variants and variants[0][1] == "error":
                self._panel.show_error(variants[0][0])
            else:
                self._panel.show_results(variants)
            self._page.update()
        except asyncio.CancelledError:
            self._panel.show_error("Translation cancelled.")
            self._page.update()
        finally:
            self._running_task = None
            self._panel.set_translating(False)
            self._page.update()
