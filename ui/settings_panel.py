"""Settings panel UI."""

import flet as ft

from ui.typography import clamp_font_scale, scale_control_fonts

FONT_FAMILY_OPTIONS: list[tuple[str, str]] = [
    ("System default", ""),
    ("Sans-serif", "sans-serif"),
    ("Serif", "serif"),
    ("Monospace", "monospace"),
]


class SettingsPanel:
    """Panel for app settings persisted across sessions."""

    def __init__(
        self,
        on_default_model_change,
        all_languages,
        on_enabled_languages_change,
        on_font_scale_change,
        on_font_family_change,
    ):
        self._all_languages = list(all_languages)
        self._on_enabled_languages_change = on_enabled_languages_change
        self._on_font_scale_change = on_font_scale_change
        self._on_font_family_change = on_font_family_change
        self._selected_languages = []
        self._page: ft.Page | None = None
        self._font_scale = 1.0

        self._model_status = ft.Text(value="Loading models...", size=11, color=ft.Colors.GREY)
        self._default_model_dropdown = ft.Dropdown(
            label="Default model",
            width=300,
            on_select=lambda e: on_default_model_change(e.control.value or ""),
        )

        self._font_family_dropdown = ft.Dropdown(
            label="Font type",
            width=220,
            options=[ft.dropdown.Option(token, label) for label, token in FONT_FAMILY_OPTIONS],
            value="",
            on_select=lambda e: self._on_font_family_change(e.control.value or ""),
        )
        self._font_scale_label = ft.Text(value="Font size: 100%", size=12, color=ft.Colors.GREY)
        self._font_scale_slider = ft.Slider(
            min=0.9,
            max=1.6,
            divisions=14,
            value=1.0,
            width=220,
            on_change=lambda e: self._set_scale_label(float(e.control.value or 1.0)),
            on_change_end=lambda e: self._on_font_scale_change(float(e.control.value or 1.0)),
        )

        self._languages_summary = ft.Text(size=12, color=ft.Colors.GREY)
        self._selected_languages_chips = ft.Row(spacing=6, wrap=True)
        self._edit_languages_btn = ft.OutlinedButton(
            "Edit languages",
            icon=ft.icons.Icons.TUNE,
            on_click=self._open_language_dialog,
        )

        self.view = ft.Column(
            controls=[
                ft.Text("Settings", size=20, weight=ft.FontWeight.W_600),
                ft.Text(
                    "Default model used for LLM interactions.",
                    size=12,
                    color=ft.Colors.GREY,
                ),
                ft.Container(height=8),
                ft.Row(
                    controls=[self._default_model_dropdown, self._model_status],
                    spacing=15,
                    alignment=ft.MainAxisAlignment.START,
                    wrap=True,
                ),
                ft.Container(height=20),
                ft.Text("Accessibility", size=14, weight=ft.FontWeight.W_600),
                ft.Text(
                    "Adjust font type and size for better readability.",
                    size=12,
                    color=ft.Colors.GREY,
                ),
                ft.Row(
                    controls=[self._font_family_dropdown, self._font_scale_slider],
                    spacing=15,
                    alignment=ft.MainAxisAlignment.START,
                    wrap=True,
                ),
                self._font_scale_label,
                ft.Container(height=20),
                ft.Text("Available languages", size=14, weight=ft.FontWeight.W_600),
                ft.Text(
                    "Choose which languages appear in New Assessment and Practice mode.",
                    size=12,
                    color=ft.Colors.GREY,
                ),
                self._languages_summary,
                self._selected_languages_chips,
                self._edit_languages_btn,
            ],
            spacing=8,
            expand=True,
            scroll=ft.ScrollMode.AUTO,
        )

    def bind_page(self, page: ft.Page) -> None:
        self._page = page

    @property
    def selected_default_model(self) -> str:
        return self._default_model_dropdown.value or ""

    @selected_default_model.setter
    def selected_default_model(self, value: str) -> None:
        self._default_model_dropdown.value = value

    def set_model_status(self, message: str, is_error: bool = False) -> None:
        self._model_status.value = message
        self._model_status.color = ft.Colors.RED if is_error else ft.Colors.GREY
        self._model_status.visible = True

    def hide_model_status(self) -> None:
        self._model_status.visible = False

    def set_models(self, names: list[str], preferred_model: str | None = None) -> None:
        self._default_model_dropdown.options = [ft.dropdown.Option(n) for n in names]
        if not names:
            self._default_model_dropdown.value = None
            return
        if preferred_model and preferred_model in names:
            self._default_model_dropdown.value = preferred_model
        else:
            self._default_model_dropdown.value = names[0]

    def set_font_scale(self, scale: float) -> None:
        safe_scale = clamp_font_scale(scale)
        self._font_scale_slider.value = safe_scale
        self._set_scale_label(safe_scale)

    def set_font_family(self, font_family: str) -> None:
        allowed = {value for _, value in FONT_FAMILY_OPTIONS}
        self._font_family_dropdown.value = font_family if font_family in allowed else ""

    def apply_typography(self, scale: float) -> None:
        self._font_scale = clamp_font_scale(scale)
        self._default_model_dropdown.width = int(300 + (self._font_scale - 1.0) * 100)
        self._font_family_dropdown.width = int(220 + (self._font_scale - 1.0) * 80)
        self._font_scale_slider.width = int(220 + (self._font_scale - 1.0) * 80)
        scale_control_fonts(self.view, self._font_scale)

    def set_selected_languages(self, languages: list[str]) -> None:
        valid = [lang for lang in languages if lang in self._all_languages]
        if not valid:
            valid = self._all_languages[:1]
        self._selected_languages = valid
        self._refresh_selected_language_ui()

    def _set_scale_label(self, scale: float) -> None:
        percent = int(round(clamp_font_scale(scale) * 100))
        self._font_scale_label.value = f"Font size: {percent}%"

    def _refresh_selected_language_ui(self) -> None:
        count = len(self._selected_languages)
        self._languages_summary.value = f"{count} language{'s' if count != 1 else ''} selected"
        self._selected_languages_chips.controls = [
            ft.Chip(
                label=ft.Text(lang, size=12),
                disabled=True,
                bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
            )
            for lang in self._selected_languages
        ]
        scale_control_fonts(self._selected_languages_chips, self._font_scale)

    def _open_language_dialog(self, _: ft.ControlEvent) -> None:
        if self._page is None:
            return

        working_selection = set(self._selected_languages)
        search_field = ft.TextField(
            label="Search languages",
            hint_text="Type to filter...",
            autofocus=True,
        )
        checklist = ft.Column(spacing=2, scroll=ft.ScrollMode.AUTO, height=340)

        def render_list() -> None:
            query = (search_field.value or "").strip().lower()
            visible = [
                lang for lang in self._all_languages if not query or query in lang.lower()
            ]

            checklist.controls = [
                ft.Checkbox(
                    label=lang,
                    value=lang in working_selection,
                    on_change=lambda ev, l=lang: toggle_language(l, bool(ev.control.value)),
                )
                for lang in visible
            ]

            if not visible:
                checklist.controls = [
                    ft.Text("No matches.", size=12, color=ft.Colors.GREY)
                ]
            scale_control_fonts(checklist, self._font_scale)

        def toggle_language(language: str, checked: bool) -> None:
            if checked:
                working_selection.add(language)
            else:
                if len(working_selection) == 1 and language in working_selection:
                    return
                working_selection.discard(language)
            render_list()
            self._page.update()

        def select_all(_: ft.ControlEvent) -> None:
            working_selection.update(self._all_languages)
            render_list()
            self._page.update()

        def clear_all(_: ft.ControlEvent) -> None:
            working_selection.clear()
            if self._all_languages:
                working_selection.add(self._all_languages[0])
            render_list()
            self._page.update()

        dialog = ft.AlertDialog(modal=True)

        def cancel(_: ft.ControlEvent) -> None:
            self._page.pop_dialog()

        def save(_: ft.ControlEvent) -> None:
            selected = [lang for lang in self._all_languages if lang in working_selection]
            if not selected and self._all_languages:
                selected = [self._all_languages[0]]
            self.set_selected_languages(selected)
            self._on_enabled_languages_change(selected)
            self._page.pop_dialog()

        search_field.on_change = lambda _: (render_list(), self._page.update())

        dialog.title = ft.Text("Available languages")
        dialog.content = ft.Container(
            content=ft.Column(
                controls=[
                    search_field,
                    ft.Row(
                        controls=[
                            ft.TextButton("Select all", on_click=select_all),
                            ft.TextButton("Clear", on_click=clear_all),
                        ]
                    ),
                    checklist,
                ],
                spacing=8,
                width=460,
            ),
            width=460,
            height=430,
        )
        dialog.actions = [
            ft.TextButton("Cancel", on_click=cancel),
            ft.FilledButton("Save", on_click=save),
        ]
        dialog.actions_alignment = ft.MainAxisAlignment.END

        render_list()
        scale_control_fonts(dialog, self._font_scale)
        self._page.show_dialog(dialog)
