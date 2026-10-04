"""Morpheme analysis panel — input text and morpheme-by-morpheme breakdown."""

import flet as ft

from core.languages import DEFAULT_ENABLED_LANGUAGES
from ui.controls import language_dropdown, set_dropdown_languages
from ui.responsive import (
    responsive_container,
    bind_responsive_container,
    responsive_button_row,
)

TEXTFIELD_BORDER_COLOR = ft.Colors.OUTLINE
TEXTFIELD_FOCUSED_BORDER_COLOR = ft.Colors.PRIMARY

INPUT_WIDTH_DESKTOP = 700
INPUT_WIDTH_TABLET = 580
INPUT_WIDTH_PHONE = None  # Full width on phone


class MorphemePanel:
    """Encapsulates the text input, controls, and morpheme analysis results."""

    def __init__(self):
        self._lang_dropdown = language_dropdown(
            DEFAULT_ENABLED_LANGUAGES, width=200, value="Serbian"
        )
        self._analyze_btn = ft.Button(
            "Analyze", icon=ft.icons.Icons.ANALYTICS, width=130
        )
        self._analyzing_indicator = ft.ProgressRing(
            width=20, height=20, visible=False, stroke_width=2
        )

        # Input text field
        self._txt_input = ft.TextField(
            label="Text to analyze…",
            hint_text="Type or paste text to analyze morpheme-by-morpheme, then click Analyze…",
            multiline=True,
            min_lines=8,
            max_lines=15,
            text_size=14,
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

        # Control rows
        self._lang_row = responsive_button_row(
            controls=[self._lang_dropdown],
            spacing=15,
        )
        self._action_row = responsive_button_row(
            controls=[self._analyze_btn, self._analyzing_indicator],
            spacing=15,
        )

        # Error display
        self._error_text = ft.Text(
            value="",
            size=13,
            color=ft.Colors.ORANGE,
            selectable=True,
            visible=False,
        )

        # Results area - morpheme table
        self._morpheme_headers = ft.Row(
            controls=[
                ft.Text("#", size=12, weight=ft.FontWeight.W_600, width=40),
                ft.Text("Morpheme", size=12, weight=ft.FontWeight.W_600, expand=True),
                ft.Text("Gloss", size=12, weight=ft.FontWeight.W_600, expand=True),
                ft.Text("Meaning", size=12, weight=ft.FontWeight.W_600, expand=True),
                ft.Text("Romanization", size=12, weight=ft.FontWeight.W_600, expand=True),
            ],
            spacing=8,
            visible=False,
        )

        self._morpheme_rows = ft.Column(controls=[], spacing=4)
        self._morpheme_table_container = ft.Container(
            content=ft.Column(
                controls=[self._morpheme_headers, self._morpheme_rows],
                spacing=6,
                scroll=ft.ScrollMode.AUTO,
            ),
            visible=False,
            border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
            border_radius=8,
            padding=10,
        )

        # Translations area
        self._translations_header = ft.Text(
            "Natural English Translations", size=15, weight=ft.FontWeight.W_600, visible=False
        )
        self._translations_column = ft.Column(controls=[], spacing=8)
        self._translations_container = ft.Container(
            content=self._translations_column,
            visible=False,
            border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
            border_radius=8,
            padding=10,
        )

        self.view = ft.Column(
            controls=[
                ft.Text("Morpheme Analysis", size=20, weight=ft.FontWeight.W_600),
                ft.Container(height=4),
                self._txt_input_container,
                ft.Container(height=8),
                self._lang_row,
                ft.Container(height=8),
                self._action_row,
                ft.Container(height=8),
                self._error_text,
                ft.Container(height=8),
                self._morpheme_table_container,
                ft.Container(height=8),
                self._translations_header,
                self._translations_container,
            ],
            expand=True,
            spacing=4,
            scroll=ft.ScrollMode.AUTO,
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

    # -- state --

    def set_analyzing(self, analyzing: bool) -> None:
        self._analyzing_indicator.visible = analyzing
        if analyzing:
            self._analyze_btn.text = "Cancel"
            self._analyze_btn.icon = ft.icons.Icons.CLOSE
        else:
            self._analyze_btn.text = "Analyze"
            self._analyze_btn.icon = ft.icons.Icons.ANALYTICS
            self._analyze_btn.disabled = False

    def set_languages(self, languages: list[str]) -> None:
        """Replace available languages and keep a valid selected value."""
        set_dropdown_languages(self._lang_dropdown, languages)

    # -- results --

    def show_results(self, morphemes: list[dict], translations: list[str]) -> None:
        self._error_text.visible = False
        self._error_text.value = ""

        # Clear previous results
        self._morpheme_rows.controls.clear()
        self._translations_column.controls.clear()

        if not morphemes:
            self._morpheme_headers.visible = False
            self._morpheme_table_container.visible = False
            self._translations_header.visible = False
            self._translations_container.visible = False
            return

        # Build morpheme rows
        self._morpheme_headers.visible = True
        for idx, m in enumerate(morphemes, start=1):
            self._morpheme_rows.controls.append(
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Text(str(idx), size=12, width=40),
                            ft.Text(
                                m.get("morpheme", ""),
                                size=13,
                                selectable=True,
                                expand=True,
                                no_wrap=False,
                            ),
                            ft.Text(
                                m.get("gloss", ""),
                                size=12,
                                selectable=True,
                                color=ft.Colors.BLUE_200,
                                expand=True,
                                no_wrap=False,
                            ),
                            ft.Text(
                                m.get("meaning", ""),
                                size=12,
                                selectable=True,
                                expand=True,
                                no_wrap=False,
                            ),
                            ft.Text(
                                m.get("romanization", ""),
                                size=12,
                                selectable=True,
                                color=ft.Colors.GREEN_200,
                                expand=True,
                                no_wrap=False,
                            ),
                        ],
                        spacing=8,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
                    border_radius=5,
                    padding=ft.padding.Padding(left=8, top=6, right=8, bottom=6),
                    bgcolor=ft.Colors.SURFACE_CONTAINER_LOWEST,
                )
            )

        self._morpheme_table_container.visible = True

        # Build translations
        if translations:
            self._translations_header.visible = True
            for idx, t in enumerate(translations, start=1):
                self._translations_column.controls.append(
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.Text(
                                    f"{idx}.",
                                    size=13,
                                    weight=ft.FontWeight.W_700,
                                    width=24,
                                ),
                                ft.Text(
                                    t,
                                    size=13,
                                    selectable=True,
                                    expand=True,
                                ),
                            ],
                            spacing=8,
                            vertical_alignment=ft.CrossAxisAlignment.START,
                        ),
                        border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
                        border_radius=8,
                        padding=ft.padding.Padding(left=12, top=10, right=12, bottom=10),
                        bgcolor=ft.Colors.SURFACE_CONTAINER_LOW,
                    )
                )
            self._translations_container.visible = True

    def show_error(self, message: str) -> None:
        self._error_text.value = message
        self._error_text.visible = bool(message)
        self._morpheme_headers.visible = False
        self._morpheme_table_container.visible = False
        self._translations_header.visible = False
        self._translations_container.visible = False

    def clear_results(self) -> None:
        self._error_text.value = ""
        self._error_text.visible = False
        self._morpheme_rows.controls.clear()
        self._morpheme_headers.visible = False
        self._morpheme_table_container.visible = False
        self._translations_column.controls.clear()
        self._translations_header.visible = False
        self._translations_container.visible = False

    def bind_page(self, page: ft.Page) -> None:
        """Bind responsive containers to page resize events."""
        bind_responsive_container(page, self._txt_input_container)