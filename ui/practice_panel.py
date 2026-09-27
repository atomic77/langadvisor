"""Interactive practice panel with translation exercise flow."""

import flet as ft

from core.languages import DEFAULT_ENABLED_LANGUAGES
from ui.controls import (
    category_dropdown,
    ects_dropdown,
    formality_dropdown,
    language_dropdown,
    set_dropdown_languages,
)
from ui.responsive import (
    responsive_container,
    bind_responsive_container,
    responsive_button_row,
)


class PracticePanel:
    """Translation practice panel with phrase generation and checking."""

    def __init__(self):
        # --- Language dropdown ---
        self._lang_dropdown = language_dropdown(
            DEFAULT_ENABLED_LANGUAGES, width=250, value="Serbian"
        )

        # --- Formality dropdown ---
        self._formality_dropdown = formality_dropdown(width=150)

        # --- Category dropdown ---
        self._category_dropdown = category_dropdown(width=350)

        # --- Generate controls ---
        self._ects_dropdown = ects_dropdown(width=250)
        self._latinization_checkbox = ft.Checkbox(
            label="Latinization",
            value=False,
            tooltip="Show standard romanization for non-Latin scripts when available.",
        )
        self._generate_btn = ft.Button("Generate", icon=ft.icons.Icons.AUTO_AWESOME, width=130)
        self._generating_indicator = ft.ProgressRing(
            width=20, height=20, visible=False, stroke_width=2
        )

        # --- Source phrase display ---
        self._source_box = responsive_container(
            width_desktop=580,
            width_tablet=520,
            width_phone=None,
            content=ft.Container(
                content=ft.Text(
                    "Click Generate to get a phrase.",
                    size=14,
                    italic=True,
                    color=ft.Colors.GREY,
                ),
                border=ft.Border.all(1, ft.Colors.OUTLINE),
                border_radius=5,
                padding=ft.padding.Padding(left=12, top=10, right=12, bottom=10),
            ),
        )
        self._romanization_text = ft.Text(
            value="", size=13, selectable=True, color=ft.Colors.BLUE_200
        )
        self._romanization_box = responsive_container(
            width_desktop=580,
            width_tablet=520,
            width_phone=None,
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text(
                            "Latinization",
                            size=11,
                            weight=ft.FontWeight.W_600,
                            color=ft.Colors.GREY,
                        ),
                        self._romanization_text,
                    ],
                    spacing=3,
                ),
                border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
                border_radius=5,
                padding=ft.padding.Padding(left=12, top=8, right=12, bottom=8),
            ),
            visible=False,
        )

        # --- User translation input ---
        self._translation_input = ft.TextField(
            label="Your translation...",
            hint_text="Type your translation here...",
            multiline=True,
            min_lines=4,
            max_lines=8,
            text_size=14,
            border_color=ft.Colors.OUTLINE,
            focused_border_color=ft.Colors.PRIMARY,
            border_width=1.2,
            focused_border_width=1.8,
        )
        self._translation_input_container = responsive_container(
            width_desktop=580,
            width_tablet=520,
            width_phone=None,
            content=self._translation_input,
        )

        # --- Check/help buttons ---
        self._check_btn = ft.Button("Check", icon=ft.icons.Icons.CHECK, width=130)
        self._help_btn = ft.Button("Help", icon=ft.icons.Icons.LIGHTBULB_OUTLINE, width=130)
        self._check_indicator = ft.ProgressRing(
            width=20, height=20, visible=False, stroke_width=2
        )

        # --- Output area (mistakes + help translation) ---
        self._mistakes_text = ft.Text(
            value="",
            size=13,
            selectable=True,
            color=ft.Colors.RED_300,
            weight=ft.FontWeight.W_500,
        )
        self._help_text = ft.Text(
            value="",
            size=13,
            selectable=True,
            color=ft.Colors.BLUE_200,
        )
        self._output_column = ft.Column(
            controls=[
                ft.Text(
                    "Mistakes:",
                    size=12,
                    weight=ft.FontWeight.W_600,
                    color=ft.Colors.RED_200,
                ),
                self._mistakes_text,
                ft.Container(height=6),
                ft.Text(
                    "Help:",
                    size=12,
                    weight=ft.FontWeight.W_600,
                    color=ft.Colors.BLUE_200,
                ),
                self._help_text,
            ],
            spacing=2,
            scroll=ft.ScrollMode.AUTO,
        )
        self._output_box = responsive_container(
            width_desktop=580,
            width_tablet=520,
            width_phone=None,
            content=ft.Container(
                content=self._output_column,
                height=140,
                visible=False,
                border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
                border_radius=5,
                padding=8,
            ),
        )

        self.view = ft.Column(
            controls=[
                ft.Text("Practice Mode", size=20, weight=ft.FontWeight.W_600),
                ft.Container(height=5),
                responsive_button_row(
                    controls=[
                        self._lang_dropdown,
                        self._formality_dropdown,
                        self._category_dropdown,
                    ],
                    spacing=15,
                ),
                responsive_button_row(
                    controls=[
                        self._ects_dropdown,
                        self._latinization_checkbox,
                        self._generate_btn,
                        self._generating_indicator,
                    ],
                    spacing=15,
                ),
                ft.Container(height=10),
                ft.Text("Translate this phrase:", size=13, weight=ft.FontWeight.W_500),
                ft.Container(height=4),
                self._source_box,
                self._romanization_box,
                ft.Container(height=10),
                self._translation_input_container,
                ft.Container(height=10),
                responsive_button_row(
                    controls=[
                        self._check_btn,
                        self._help_btn,
                        self._check_indicator,
                    ],
                    spacing=10,
                ),
                ft.Container(height=8),
                self._output_box,
            ],
            expand=True,
            spacing=6,
        )

    # -- properties --

    @property
    def selected_language(self) -> str:
        return self._lang_dropdown.value or ""

    @property
    def selected_formality(self) -> str:
        return self._formality_dropdown.value or ""

    @property
    def selected_category(self) -> str:
        return self._category_dropdown.value or ""

    @property
    def selected_ects_level(self) -> str:
        return self._ects_dropdown.value or ""

    @property
    def latinization_enabled(self) -> bool:
        return bool(self._latinization_checkbox.value)

    # -- state --

    def set_generating(self, generating: bool) -> None:
        self._generating_indicator.visible = generating
        if generating:
            self._generate_btn.text = "Cancel"
            self._generate_btn.icon = ft.icons.Icons.CLOSE
            self._latinization_checkbox.disabled = True
        else:
            self._generate_btn.text = "Generate"
            self._generate_btn.icon = ft.icons.Icons.AUTO_AWESOME
            self._generate_btn.disabled = False
            self._latinization_checkbox.disabled = False

    def set_checking(self, checking: bool) -> None:
        self._check_indicator.visible = checking
        self._help_btn.disabled = checking
        if checking:
            self._check_btn.text = "Cancel"
            self._check_btn.icon = ft.icons.Icons.CLOSE
        else:
            self._check_btn.text = "Check"
            self._check_btn.icon = ft.icons.Icons.CHECK
            self._check_btn.disabled = False

    def set_languages(self, languages: list[str]) -> None:
        """Replace available languages and keep a valid selected value."""
        set_dropdown_languages(self._lang_dropdown, languages)

    def bind_page(self, page: ft.Page) -> None:
        """Bind responsive containers to page resize events."""
        bind_responsive_container(page, self._source_box)
        bind_responsive_container(page, self._romanization_box)
        bind_responsive_container(page, self._translation_input_container)
        bind_responsive_container(page, self._output_box)

    @property
    def source_phrase(self) -> str:
        return self._source_box.content.value or ""

    @property
    def translation_text(self) -> str:
        return self._translation_input.value or ""

    def clear_output(self) -> None:
        self._mistakes_text.value = ""
        self._mistakes_text.color = ft.Colors.RED_300
        self._help_text.value = ""
        self._output_box.visible = False

    def clear_romanization(self) -> None:
        self._romanization_text.value = ""
        self._romanization_box.visible = False

    def set_source_phrase(self, phrase: str, romanization: str = "") -> None:
        self._source_box.content.value = phrase
        self._source_box.content.color = ft.Colors.ON_SURFACE
        self._source_box.content.italic = False
        self._romanization_text.value = romanization
        self._romanization_box.visible = bool(romanization.strip())
        self._translation_input.value = ""
        self.clear_output()

    def show_mistakes(self, mistakes: str) -> None:
        self._mistakes_text.value = mistakes
        self._mistakes_text.color = ft.Colors.RED_300
        self._output_box.visible = bool(mistakes or self._help_text.value)

    def show_help(self, translation: str) -> None:
        self._help_text.value = translation
        self._output_box.visible = bool(self._mistakes_text.value or translation)
