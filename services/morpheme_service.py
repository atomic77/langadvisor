"""Morpheme analysis service — coordinates LLM calls and UI updates for the Morpheme panel."""

import asyncio

from core.llm import analyze_morphemes, get_default_model


class MorphemeService:
    """Handles running morpheme analysis and updating the panel."""

    def __init__(self, panel, page):
        self._panel = panel
        self._page = page
        self._running_task = None

    async def on_analyze(self, e) -> None:
        if self._running_task is not None and not self._running_task.done():
            self._running_task.cancel()
            self._running_task = None
            self._panel.set_analyzing(False)
            self._panel.show_error("Analysis cancelled.")
            self._page.update()
            return

        text = self._panel.input_text
        if not text.strip():
            return

        language = self._panel.selected_language
        if not language:
            self._panel.show_error("Please pick a language.")
            self._page.update()
            return

        self._panel.set_analyzing(True)
        self._panel.clear_results()
        self._page.update()

        model = get_default_model() or ""

        self._running_task = asyncio.current_task()
        try:
            result = await analyze_morphemes(text, language, model)

            if result.get("error"):
                self._panel.show_error(result["error"])
            else:
                self._panel.show_results(result.get("morphemes", []), result.get("translations", []))
            self._page.update()
        except asyncio.CancelledError:
            self._panel.show_error("Analysis cancelled.")
            self._page.update()
        finally:
            self._running_task = None
            self._panel.set_analyzing(False)
            self._page.update()