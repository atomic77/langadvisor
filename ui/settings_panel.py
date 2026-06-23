"""Settings panel UI."""

import flet as ft


class SettingsPanel:
    """Panel for app settings persisted across sessions."""

    def __init__(self, on_default_model_change, all_languages, on_enabled_languages_change):
        self._all_languages = list(all_languages)
        self._on_enabled_languages_change = on_enabled_languages_change
        self._selected_languages = []
        self._page: ft.Page | None = None

        self._model_status = ft.Text(value="Loading models…", size=11, color=ft.Colors.GREY)
        self._default_model_dropdown = ft.Dropdown(
            label="Default model",
            width=300,
            on_select=lambda e: on_default_model_change(e.control.value or ""),
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
                ),
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

    def set_selected_languages(self, languages: list[str]) -> None:
        valid = [lang for lang in languages if lang in self._all_languages]
        if not valid:
            valid = self._all_languages[:1]
        self._selected_languages = valid
        self._refresh_selected_language_ui()

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
        self._page.show_dialog(dialog)
