"""Translation panel — input and translation variants in a responsive layout."""

import flet as ft

from core.languages import DEFAULT_ENABLED_LANGUAGES
from ui.controls import formality_dropdown, language_dropdown, set_dropdown_languages
from ui.responsive import register_resize_handler

TEXTFIELD_BORDER_COLOR = ft.Colors.OUTLINE
TEXTFIELD_FOCUSED_BORDER_COLOR = ft.Colors.PRIMARY

AUTO_DETECT = "Auto-detect"
DEFAULT_VARIATION_COUNT = 5
MIN_VARIATION_COUNT = 1
MAX_VARIATION_COUNT = 10

class TranslationPanel:
    """Encapsulates source text, language/formality/count selectors, and a results column."""

    def __init__(self):
        self._page: ft.Page | None = None
        self._stacked = False
        # --- Input column (left) ---
        self._txt_input = ft.TextField(
            label="Text to translate…",
            hint_text="Type or paste the source text here, then click Translate (or press Ctrl+Enter)…",
            multiline=True,
            min_lines=6,
            max_lines=12,
            text_size=14,
            border_color=TEXTFIELD_BORDER_COLOR,
            focused_border_color=TEXTFIELD_FOCUSED_BORDER_COLOR,
            border_width=1.2,
            focused_border_width=1.8,
        )

        # Source language includes an "Auto-detect" option as the first choice.
        self._source_lang_dropdown = ft.Dropdown(
            label="From",
            width=180,
            value=AUTO_DETECT,
            options=[ft.dropdown.Option(AUTO_DETECT, AUTO_DETECT)]
            + [ft.dropdown.Option(lang, lang) for lang in DEFAULT_ENABLED_LANGUAGES],
        )
        self._target_lang_dropdown = language_dropdown(
            DEFAULT_ENABLED_LANGUAGES, width=180, value="English"
        )
        self._formality_dropdown = formality_dropdown(width=180)
        self._count_field = ft.TextField(
            label="Variations",
            value=str(DEFAULT_VARIATION_COUNT),
            width=110,
            text_size=14,
            input_filter=ft.NumbersOnlyInputFilter(),
            border_color=TEXTFIELD_BORDER_COLOR,
            focused_border_color=TEXTFIELD_FOCUSED_BORDER_COLOR,
            border_width=1.2,
            focused_border_width=1.8,
        )

        self._translate_btn = ft.Button(
            "Translate", icon=ft.icons.Icons.TRANSLATE, width=130
        )
        self._translating_indicator = ft.ProgressRing(
            width=20, height=20, visible=False, stroke_width=2
        )

        self._error_text = ft.Text(
            value="",
            size=13,
            color=ft.Colors.ORANGE,
            selectable=True,
            visible=False,
        )

        # --- Results column (right) ---
        self._results_header = ft.Text(
            "Translations", size=15, weight=ft.FontWeight.W_600
        )
        self._results_placeholder = ft.Text(
            "Translations will appear here.",
            size=13,
            italic=True,
            color=ft.Colors.GREY,
        )
        self._results_column = ft.Column(
            controls=[self._results_placeholder],
            spacing=10,
            scroll=ft.ScrollMode.AUTO,
        )
        self._results_box = ft.Container(
            content=self._results_column,
            expand=True,
            border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
            border_radius=8,
            padding=10,
        )

        # --- Build the two content columns (independent of layout) ---
        self._left_column = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("Translation Mode", size=20, weight=ft.FontWeight.W_600),
                    ft.Container(height=4),
                    self._txt_input,
                    ft.Container(height=10),
                    self._source_lang_dropdown,
                    ft.Container(height=8),
                    self._target_lang_dropdown,
                    ft.Container(height=8),
                    self._formality_dropdown,
                    ft.Container(height=8),
                    self._count_field,
                    ft.Container(height=14),
                    ft.Row(
                        controls=[
                            self._translate_btn,
                            self._translating_indicator,
                        ],
                        alignment=ft.MainAxisAlignment.START,
                        spacing=12,
                    ),
                    ft.Container(height=6),
                    self._error_text,
                ],
                spacing=2,
            ),
            width=400,
            padding=ft.padding.Padding(right=8, top=0, left=0, bottom=0),
        )
        self._right_column = ft.Column(
            controls=[
                self._results_header,
                ft.Container(height=6),
                self._results_box,
            ],
            expand=True,
            spacing=4,
        )

        # --- Responsive root: Row (landscape/desktop) or Column (portrait) ---
        self._root_row = ft.Row(
            controls=[self._left_column, self._right_column],
            expand=True,
            vertical_alignment=ft.CrossAxisAlignment.START,
            spacing=12,
        )
        self._root_column = ft.Column(
            controls=[self._left_column, self._right_column],
            expand=True,
            spacing=16,
            scroll=ft.ScrollMode.AUTO,
        )
        self.view = ft.Container(content=self._root_row, expand=True)

    def bind_page(self, page: ft.Page) -> None:
        """Attach page reference and register resize handler."""
        self._page = page
        register_resize_handler(page, self._on_resize)
        self._apply_layout(page.width, page.height)

    def _on_resize(self, e: ft.PageResizeEvent) -> None:
        self._apply_layout(e.width, e.height)

    def _apply_layout(self, width: float, height: float) -> None:
        """Stack columns when the page cannot fit both panels side by side."""
        if width <= 0 or height <= 0:
            return
        stacked = width < 900
        if stacked != self._stacked:
            self._stacked = stacked
            self.view.content = self._root_column if stacked else self._root_row
            self._left_column.width = None if stacked else 400
            self._right_column.expand = not stacked
            self._results_box.expand = not stacked
            self._results_box.height = 260 if stacked else None

    # -- properties exposed for the service --

    @property
    def input_text(self) -> str:
        return self._txt_input.value or ""

    @property
    def selected_source_language(self) -> str:
        return self._source_lang_dropdown.value or AUTO_DETECT

    @property
    def selected_target_language(self) -> str:
        return self._target_lang_dropdown.value or ""

    @property
    def selected_formality(self) -> str:
        return self._formality_dropdown.value or ""

    @property
    def variation_count(self) -> int:
        raw = (self._count_field.value or "").strip()
        try:
            n = int(raw)
        except ValueError:
            return DEFAULT_VARIATION_COUNT
        return max(MIN_VARIATION_COUNT, min(MAX_VARIATION_COUNT, n))

    # -- state --

    def set_translating(self, translating: bool) -> None:
        self._translating_indicator.visible = translating
        if translating:
            self._translate_btn.text = "Cancel"
            self._translate_btn.icon = ft.icons.Icons.CLOSE
        else:
            self._translate_btn.text = "Translate"
            self._translate_btn.icon = ft.icons.Icons.TRANSLATE
            self._translate_btn.disabled = False

    def set_languages(self, languages: list[str]) -> None:
        """Rebuild source/target dropdowns while preserving valid selections.

        Source keeps "Auto-detect" pinned at index 0; target starts from the
        first enabled language (no Auto-detect option).
        """
        # Source dropdown.
        current_source = self._source_lang_dropdown.value
        self._source_lang_dropdown.options = (
            [ft.dropdown.Option(AUTO_DETECT, AUTO_DETECT)]
            + [ft.dropdown.Option(lang, lang) for lang in languages]
        )
        if current_source == AUTO_DETECT or current_source in languages:
            self._source_lang_dropdown.value = current_source
        else:
            self._source_lang_dropdown.value = AUTO_DETECT

        # Target dropdown.
        set_dropdown_languages(self._target_lang_dropdown, languages)

    # -- results --

    def show_results(self, variants: list[tuple[str, str]]) -> None:
        self._error_text.visible = False
        self._error_text.value = ""
        if not variants:
            self._results_column.controls = [self._results_placeholder]
            return
        self._results_column.controls = [
            self._build_variant_card(idx, translation, tag)
            for idx, (translation, tag) in enumerate(variants, start=1)
        ]

    def show_error(self, message: str) -> None:
        self._error_text.value = message
        self._error_text.visible = bool(message)

    def clear_results(self) -> None:
        self._results_column.controls = [self._results_placeholder]
        self._error_text.value = ""
        self._error_text.visible = False

    def _build_variant_card(
        self, idx: int, translation: str, tag: str
    ) -> ft.Container:
        tag_chip = ft.Container(
            content=ft.Text(
                tag or "—",
                size=11,
                color=ft.Colors.WHITE,
                weight=ft.FontWeight.W_600,
            ),
            bgcolor=ft.Colors.BLUE_400,
            border_radius=3,
            padding=ft.padding.Padding(left=6, top=2, right=6, bottom=2),
            visible=bool(tag),
        )
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Text(
                                f"{idx}.",
                                size=13,
                                weight=ft.FontWeight.W_700,
                            ),
                            tag_chip,
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Container(height=6),
                    ft.Text(
                        translation,
                        size=14,
                        selectable=True,
                    ),
                ],
                spacing=2,
            ),
            border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
            border_radius=8,
            padding=ft.padding.Padding(left=14, top=12, right=14, bottom=12),
            bgcolor=ft.Colors.SURFACE_CONTAINER_LOW,
        )
