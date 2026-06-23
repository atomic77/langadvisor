"""Top-level application layout and wiring."""

import asyncio
import threading

import flet as ft

from core.history_store import HistoryStore
from core.model_fetcher import fetch_ollama_models
from services.assessor import AssessorService
from ui.assessment_panel import AssessmentPanel
from ui.sidebar import Sidebar


_loading_from_history = False


def main(page: ft.Page):
    page.title = "Grammar Assessor"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 20

    store = HistoryStore()

    def _new_assessment():
        global _loading_from_history
        _loading_from_history = True
        panel.input_text = ""
        panel.clear_results()
        _loading_from_history = False
        page.update()

    def _load_history(idx: int):
        global _loading_from_history
        entry = store.get(idx)
        _loading_from_history = True
        panel.input_text = entry.text
        panel.selected_language = entry.language
        panel.selected_formality = entry.formality
        panel.selected_model = entry.model
        _loading_from_history = False

        verdict = entry.verdict
        if verdict == "yes":
            panel.show_correct()
        elif verdict == "no":
            panel.show_feedback(entry.feedback, entry.suggestion)
        else:
            panel.show_error(verdict)
        page.update()

    sidebar = Sidebar(store, on_new=_new_assessment, on_load=_load_history)

    def _on_text_change(e: ft.ControlEvent):
        if not _loading_from_history:
            panel.clear_results()
            page.update()

    panel = AssessmentPanel(on_assess_click=None, on_text_change=_on_text_change, on_keyboard=None)
    service = AssessorService(store, panel, page)
    panel._assess_btn.on_click = service.on_assess

    def on_keyboard(e: ft.KeyboardEvent):
        if e.ctrl and e.key == "Enter":
            asyncio.create_task(service.on_assess(e))

    page.on_keyboard_event = on_keyboard

    def _apply_models(names):
        panel.set_models(names)
        panel.hide_model_status()
        page.update()

    def _apply_error(msg):
        panel.set_model_status(f"Could not load models: {msg}", is_error=True)
        page.update()

    def _do_fetch():
        try:
            names = fetch_ollama_models()
            page.run_thread(lambda: _apply_models(names))
        except Exception as exc:
            import traceback
            traceback.print_exc()
            page.run_thread(lambda: _apply_error(str(exc)))

    threading.Thread(target=_do_fetch, daemon=True).start()

    page.add(
        ft.Row(
            controls=[
                sidebar.view,
                ft.Container(width=15),
                panel.view,
            ],
            spacing=0,
            alignment=ft.MainAxisAlignment.START,
            expand=True,
        )
    )
