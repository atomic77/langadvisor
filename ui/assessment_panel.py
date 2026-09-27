"""Main assessment input and results panel."""

import flet as ft

from core.languages import DEFAULT_ENABLED_LANGUAGES
from ui.controls import formality_dropdown, language_dropdown, set_dropdown_languages
from ui.responsive import (
    responsive_container,
    bind_responsive_container,
    responsive_button_row,
)

TEXTFIELD_BORDER_COLOR = ft.Colors.OUTLINE
TEXTFIELD_FOCUSED_BORDER_COLOR = ft.Colors.PRIMARY

# Responsive widths
INPUT_WIDTH_DESKTOP = 580
INPUT_WIDTH_TABLET = 520
INPUT_WIDTH_PHONE = None  # Full width on phone


class AssessmentPanel:
    """Encapsulates the text input, controls, and result displays."""

    def __init__(self, on_text_change=None):
        self._lang_dropdown = language_dropdown(
            DEFAULT_ENABLED_LANGUAGES, width=150, value="Serbian"
        )
        self._formality_dropdown = formality_dropdown(width=150)
        self._assess_btn = ft.Button("Assess", icon=ft.icons.Icons.CHECK, width=130)
        self._assessing_indicator = ft.ProgressRing(
            width=20, height=20, visible=False, stroke_width=2
        )

        self._grammar_result = ft.Text(
            value="", size=15, visible=False, weight=ft.FontWeight.W_500
        )
        self._feedback_text = ft.Text(value="", size=13, selectable=True)
        self._feedback_box = responsive_container(
            width_desktop=INPUT_WIDTH_DESKTOP,
            width_tablet=INPUT_WIDTH_TABLET,
            width_phone=INPUT_WIDTH_PHONE,
            content=ft.Column(controls=[self._feedback_text], scroll=ft.ScrollMode.AUTO),
            height=120,
            visible=False,
            border=ft.Border.all(1, ft.Colors.RED_200),
            border_radius=5,
            padding=8,
        )
        self._suggestion_box = ft.TextField(
            label="Suggested correction",
            multiline=True,
            min_lines=2,
            max_lines=5,
            read_only=True,
            visible=False,
            border_color=TEXTFIELD_BORDER_COLOR,
            focused_border_color=TEXTFIELD_FOCUSED_BORDER_COLOR,
            border_width=1.2,
            focused_border_width=1.8,
        )
        self._suggestion_box_container = responsive_container(
            width_desktop=INPUT_WIDTH_DESKTOP,
            width_tablet=INPUT_WIDTH_TABLET,
            width_phone=INPUT_WIDTH_PHONE,
            content=self._suggestion_box,
        )

        self._txt_input = ft.TextField(
            label="Write your text here…",
            hint_text="Type or paste text to assess, then click Assess (or press Ctrl+Enter)…",
            multiline=True,
            min_lines=10,
            max_lines=20,
            text_size=14,
            on_change=on_text_change,
            border_color=TEXTFIELD_BORDER_COLOR,
            focused_border_color=TEXTFIELD_FOCUSED_BORDER_COLOR,
            border_width=1.2,
            focused_border_width=1.8,
        )
        self._txt_input_container = responsive_container(
            width_desktop=INPUT_WIDTH_DESKTOP,
            width_tablet=INPUT_WIDTH_TABLET,
            width_phone=INPUT_WIDTH_PHONE,
            content=self._txt_input,
        )

        # Control rows with responsive wrapping
        self._lang_row = responsive_button_row(
            controls=[self._lang_dropdown, self._formality_dropdown],
            spacing=15,
        )
        self._action_row = responsive_button_row(
            controls=[self._assess_btn, self._assessing_indicator],
            spacing=15,
        )

        self.view = ft.Column(
            controls=[
                self._txt_input_container,
                self._lang_row,
                self._action_row,
                self._grammar_result,
                self._feedback_box,
                self._suggestion_box_container,
            ],
            expand=True,
            spacing=10,
        )

    # -- properties exposed for the service --

    @property
    def input_text(self) -> str:
        return self._txt_input.value or ""

    @input_text.setter
    def input_text(self, value: str) -> None:
        self._txt_input.value = value

    @property
    def selected_language(self) -> str:
        return self._lang_dropdown.value or ""

    @selected_language.setter
    def selected_language(self, value: str) -> None:
        self._lang_dropdown.value = value

    @property
    def selected_formality(self) -> str:
        return self._formality_dropdown.value or ""

    @selected_formality.setter
    def selected_formality(self, value: str) -> None:
        self._formality_dropdown.value = value

    # -- assessment state --

    def set_assessing(self, assessing: bool) -> None:
        self._assessing_indicator.visible = assessing
        if assessing:
            self._assess_btn.text = "Cancel"
            self._assess_btn.icon = ft.icons.Icons.CLOSE
        else:
            self._assess_btn.text = "Assess"
            self._assess_btn.icon = ft.icons.Icons.CHECK
            self._assess_btn.disabled = False

    def set_languages(self, languages: list[str]) -> None:
        """Replace available languages and keep a valid selected value."""
        set_dropdown_languages(self._lang_dropdown, languages)

    # -- results --

    def show_correct(self) -> None:
        self._grammar_result.value = "✓  Grammar is correct"
        self._grammar_result.color = ft.Colors.GREEN
        self._grammar_result.visible = True
        self._feedback_box.visible = False
        self._suggestion_box.visible = False

    def show_feedback(self, feedback: str, suggestion: str) -> None:
        self._grammar_result.visible = False
        self._feedback_text.value = feedback
        self._feedback_box.visible = bool(feedback)
        self._suggestion_box.value = suggestion
        self._suggestion_box.visible = bool(suggestion)

    def show_error(self, message: str) -> None:
        self._grammar_result.value = message
        self._grammar_result.color = ft.Colors.ORANGE
        self._grammar_result.visible = True
        self._feedback_box.visible = False
        self._suggestion_box.visible = False

    def show_cancelled(self) -> None:
        self.show_error("Assessment cancelled.")

    def clear_results(self) -> None:
        self._grammar_result.visible = False
        self._feedback_text.value = ""
        self._feedback_box.visible = False
        self._suggestion_box.value = ""
        self._suggestion_box.visible = False

    def bind_page(self, page: ft.Page) -> None:
        """Bind responsive containers to page resize events."""
        bind_responsive_container(page, self._txt_input_container)
        bind_responsive_container(page, self._feedback_box)
        bind_responsive_container(page, self._suggestion_box_container)
