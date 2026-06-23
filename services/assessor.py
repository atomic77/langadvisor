"""Assessment service — coordinates LLM calls, history, and UI updates."""

import asyncio

from core.history_store import HistoryEntry, HistoryStore
from core.llm import check_grammar, get_default_model


class AssessorService:
    """Handles running assessments and updating UI + history."""

    def __init__(self, store: HistoryStore, panel, page):
        self._store = store
        self._panel = panel
        self._page = page
        self._running_task = None

    async def on_assess(self, e) -> None:
        if self._running_task is not None and not self._running_task.done():
            self._running_task.cancel()
            self._running_task = None
            self._panel.set_assessing(False)
            self._panel.show_cancelled()
            self._page.update()
            return

        text = self._panel.input_text
        if not text.strip():
            return

        self._panel.set_assessing(True)
        self._panel.clear_results()
        self._page.update()

        selected_model = self._panel.selected_model
        effective_model = selected_model or (get_default_model() or "")

        self._running_task = asyncio.current_task()
        try:
            verdict, feedback, suggestion = await check_grammar(
                text,
                self._panel.selected_language,
                self._panel.selected_formality,
                selected_model,
            )

            if verdict in ("yes", "no"):
                if verdict == "yes":
                    self._panel.show_correct()
                else:
                    self._panel.show_feedback(feedback, suggestion)
            else:
                self._panel.show_error(verdict)
            self._page.update()

            self._store.add(
                HistoryEntry(
                    text=text,
                    language=self._panel.selected_language,
                    formality=self._panel.selected_formality,
                    model=effective_model,
                    verdict=verdict,
                    feedback=feedback,
                    suggestion=suggestion,
                )
            )

        except asyncio.CancelledError:
            self._panel.show_cancelled()
            self._page.update()
        finally:
            self._running_task = None
            self._panel.set_assessing(False)
            self._page.update()
