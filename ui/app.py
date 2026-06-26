"""Top-level application layout and wiring."""

import asyncio
import threading

import flet as ft

from core.history_store import HistoryStore
from core.languages import DEFAULT_ENABLED_LANGUAGES, TOP_50_LANGUAGES
from core.lesson_store import LessonStore
from core.llm import set_default_model
from core.model_fetcher import fetch_ollama_models
from core.persistence import (
    load_default_model,
    load_enabled_languages,
    load_ui_font_family,
    load_ui_font_scale,
    save_default_model,
    save_enabled_languages,
    save_ui_font_family,
    save_ui_font_scale,
)
from services.assessor import AssessorService
from services.lesson_service import LessonService
from services.practice_service import PracticeService
from ui.assessment_panel import AssessmentPanel
from ui.lesson_panel import LessonPanel
from ui.practice_panel import PracticePanel
from ui.settings_panel import SettingsPanel
from ui.sidebar import Sidebar
from ui.typography import clamp_font_scale, scale_control_fonts


_loading_from_history = False
_active_mode = "grammar"


def main(page: ft.Page):
    page.title = "Lang Advisor"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 20

    store = HistoryStore()
    default_model = load_default_model()
    ui_font_scale = clamp_font_scale(load_ui_font_scale())
    ui_font_family = load_ui_font_family()

    available_languages = TOP_50_LANGUAGES.copy()
    selected_languages = [
        language
        for language in load_enabled_languages()
        if language in available_languages
    ]
    if not selected_languages:
        selected_languages = DEFAULT_ENABLED_LANGUAGES.copy()

    set_default_model(default_model)

    assessment_panel = AssessmentPanel(
        on_assess_click=None, on_text_change=None, on_keyboard=None
    )
    practice_panel = PracticePanel()
    lesson_panel = LessonPanel()
    assessment_panel.set_languages(selected_languages)
    practice_panel.set_languages(selected_languages)
    lesson_panel.set_languages(selected_languages)

    def _apply_ui_preferences() -> None:
        nonlocal ui_font_scale, ui_font_family

        family = ui_font_family or None
        page.theme = ft.Theme(font_family=family)
        page.dark_theme = ft.Theme(font_family=family)

        sidebar.apply_typography(ui_font_scale)
        lesson_panel.apply_typography(ui_font_scale)
        settings_panel.apply_typography(ui_font_scale)

        scale_control_fonts(assessment_panel.view, ui_font_scale)
        scale_control_fonts(practice_panel.view, ui_font_scale)
        scale_control_fonts(content_area, ui_font_scale)

        spacer.width = max(12, int(round(15 * ui_font_scale)))

    def _on_default_model_change(model: str):
        nonlocal default_model
        if not model:
            return
        default_model = model
        save_default_model(model)
        set_default_model(model)
        page.update()

    def _on_enabled_languages_change(languages: list[str]):
        assessment_panel.set_languages(languages)
        practice_panel.set_languages(languages)
        lesson_panel.set_languages(languages)
        save_enabled_languages(languages)
        page.update()

    def _on_font_scale_change(scale: float) -> None:
        nonlocal ui_font_scale
        ui_font_scale = clamp_font_scale(scale)
        settings_panel.set_font_scale(ui_font_scale)
        save_ui_font_scale(ui_font_scale)
        _apply_ui_preferences()
        page.update()

    def _on_font_family_change(font_family: str) -> None:
        nonlocal ui_font_family
        ui_font_family = font_family or ""
        settings_panel.set_font_family(ui_font_family)
        save_ui_font_family(ui_font_family)
        _apply_ui_preferences()
        page.update()

    settings_panel = SettingsPanel(
        on_default_model_change=_on_default_model_change,
        all_languages=available_languages,
        on_enabled_languages_change=_on_enabled_languages_change,
        on_font_scale_change=_on_font_scale_change,
        on_font_family_change=_on_font_family_change,
    )
    settings_panel.bind_page(page)
    settings_panel.set_selected_languages(selected_languages)
    settings_panel.set_font_scale(ui_font_scale)
    settings_panel.set_font_family(ui_font_family)

    content_area = ft.Container(content=assessment_panel.view, expand=True)

    def _switch_mode(mode: str):
        global _active_mode
        _active_mode = mode
        if mode == "practice":
            content_area.content = practice_panel.view
        elif mode == "lesson":
            content_area.content = lesson_panel.view
        elif mode == "settings":
            content_area.content = settings_panel.view
        else:
            content_area.content = assessment_panel.view
        _apply_ui_preferences()
        page.update()

    def _new_assessment():
        global _loading_from_history
        _switch_mode("grammar")
        _loading_from_history = True
        assessment_panel.input_text = ""
        assessment_panel.clear_results()
        _loading_from_history = False
        page.update()

    def _load_history(idx: int):
        global _loading_from_history
        entry = store.get(idx)
        _loading_from_history = True
        assessment_panel.input_text = entry.text
        assessment_panel.selected_language = entry.language
        assessment_panel.selected_formality = entry.formality
        _loading_from_history = False

        verdict = entry.verdict
        if verdict == "yes":
            assessment_panel.show_correct()
        elif verdict == "no":
            assessment_panel.show_feedback(entry.feedback, entry.suggestion)
        else:
            assessment_panel.show_error(verdict)
        page.update()

    sidebar = Sidebar(
        store, on_new=_new_assessment, on_load=_load_history, on_mode_change=_switch_mode
    )

    def _on_text_change(e: ft.ControlEvent):
        if not _loading_from_history:
            assessment_panel.clear_results()
            page.update()

    assessment_service = AssessorService(store, assessment_panel, page)
    assessment_panel._assess_btn.on_click = assessment_service.on_assess

    practice_service = PracticeService(practice_panel, page)
    practice_panel._generate_btn.on_click = practice_service.on_generate
    practice_panel._check_btn.on_click = practice_service.on_check
    practice_panel._help_btn.on_click = practice_service.on_help

    lesson_store = LessonStore()
    lesson_service = LessonService(lesson_panel, page, lesson_store)
    lesson_panel._start_btn.on_click = lesson_service.on_start
    lesson_panel._prev_btn.on_click = lesson_service.on_prev
    lesson_panel._next_btn.on_click = lesson_service.on_next
    lesson_panel._help_btn.on_click = lesson_service.on_help
    lesson_panel._skip_btn.on_click = lesson_service.on_skip
    lesson_panel._submit_btn.on_click = lesson_service.on_submit
    lesson_panel._reset_btn.on_click = lesson_service.on_reset

    def on_keyboard(e: ft.KeyboardEvent):
        if e.ctrl and e.key == "Enter":
            if _active_mode == "grammar":
                asyncio.create_task(assessment_service.on_assess(e))
            elif _active_mode == "lesson":
                lesson_service.on_next(e)

    page.on_keyboard_event = on_keyboard

    def _apply_models(names):
        nonlocal default_model
        if names:
            if not default_model or default_model not in names:
                default_model = names[0]
                save_default_model(default_model)
            set_default_model(default_model)
            settings_panel.set_models(names, preferred_model=default_model)
            settings_panel.hide_model_status()
        else:
            message = "No Ollama models found. Pull at least one model locally."
            settings_panel.set_model_status(message, is_error=True)
        _apply_ui_preferences()
        page.update()

    def _apply_error(msg):
        settings_panel.set_model_status(f"Could not load models: {msg}", is_error=True)
        _apply_ui_preferences()
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

    spacer = ft.Container(width=15)
    page.add(
        ft.Row(
            controls=[
                sidebar.view,
                spacer,
                content_area,
            ],
            spacing=0,
            alignment=ft.MainAxisAlignment.START,
            expand=True,
        )
    )

    _apply_ui_preferences()
