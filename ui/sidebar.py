"""Sidebar widget with history list."""

import flet as ft

from core.history_store import HistoryStore


class Sidebar:
    """Collapsible sidebar containing new/search buttons and history."""

    def __init__(
        self,
        store: HistoryStore,
        on_new: callable,
        on_load: callable,
    ):
        self._store = store
        self._on_new = on_new
        self._on_load = on_load
        self._store.on_change(self._rebuild_history_list)
        self._search_query = ""

        self._theme_btn_collapsed = ft.IconButton(
            icon=ft.icons.Icons.DARK_MODE,
            icon_size=22,
            tooltip="Toggle theme",
            on_click=lambda e: self._toggle_theme(e),
        )
        self._theme_btn_expanded = ft.IconButton(
            icon=ft.icons.Icons.DARK_MODE,
            icon_size=20,
            tooltip="Toggle theme",
            on_click=lambda e: self._toggle_theme(e),
        )

        self._history_list = ft.ListView(
            controls=[],
            expand=True,
            spacing=6,
            padding=5,
        )

        self._collapsed = ft.Container(
            content=ft.Column(
                controls=[
                    ft.IconButton(
                        icon=ft.icons.Icons.MENU,
                        icon_size=22,
                        tooltip="Expand sidebar",
                        on_click=lambda e: self.toggle(),
                    ),
                    ft.Container(height=8),
                    ft.IconButton(
                        icon=ft.icons.Icons.ADD,
                        icon_size=22,
                        tooltip="New assessment",
                        on_click=lambda e: self._on_new(),
                    ),
                    ft.IconButton(
                        icon=ft.icons.Icons.SEARCH,
                        icon_size=22,
                        tooltip="Search",
                        on_click=lambda e: self._toggle_search(e),
                    ),
                    ft.Container(height=4),
                    self._theme_btn_collapsed,
                ],
                spacing=0,
                alignment=ft.MainAxisAlignment.START,
            ),
            width=48,
            bgcolor=ft.Colors.SURFACE_CONTAINER_LOW,
            border_radius=8,
            padding=8,
            visible=True,
        )

        header = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Text("Sidebar", size=14, weight=ft.FontWeight.W_600),
                    self._theme_btn_expanded,
                    ft.IconButton(
                        icon=ft.icons.Icons.MENU_OPEN,
                        icon_size=20,
                        tooltip="Collapse sidebar",
                        on_click=lambda e: self.toggle(),
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            padding=ft.padding.Padding(bottom=6, left=0, right=0, top=0),
        )

        new_btn = ft.TextButton(
            content=ft.Row(
                [ft.Icon(ft.icons.Icons.ADD, size=16), ft.Text("New Assessment", size=13)]
            ),
            on_click=lambda e: self._on_new(),
        )
        search_btn = ft.TextButton(
            content=ft.Row(
                [ft.Icon(ft.icons.Icons.SEARCH, size=16), ft.Text("Search", size=13)]
            ),
            on_click=lambda e: self._toggle_search(e),
        )
        self._search_input = ft.TextField(
            label="Search history…",
            hint_text="Filter by text, language, model…",
            on_change=lambda e: self._apply_search(e.control.value),
            visible=False,
            dense=True,
        )
        divider = ft.Divider(height=1, color=ft.Colors.OUTLINE_VARIANT)
        history_header = ft.Text("History", size=13, weight=ft.FontWeight.W_600)

        self._expanded = ft.Container(
            content=ft.Column(
                controls=[
                    header,
                    new_btn,
                    search_btn,
                    self._search_input,
                    divider,
                    history_header,
                    self._history_list,
                ],
                spacing=6,
            ),
            width=220,
            bgcolor=ft.Colors.SURFACE_CONTAINER_LOW,
            border_radius=8,
            padding=10,
            visible=False,
        )

        self.view = ft.Row(
            controls=[self._collapsed, self._expanded],
            spacing=0,
            vertical_alignment=ft.CrossAxisAlignment.START,
        )

        # Populate the list from any pre-loaded store entries (e.g. from disk).
        self._rebuild_history_list()

    def toggle(self) -> None:
        expanded = self._expanded.visible
        self._collapsed.visible = expanded
        self._expanded.visible = not expanded

    def _toggle_theme(self, e: ft.ControlEvent) -> None:
        page = e.control.page
        # Cycle: SYSTEM/LIGHT → DARK → LIGHT → DARK → …
        current = page.theme_mode
        page.theme_mode = (
            ft.ThemeMode.DARK
            if current != ft.ThemeMode.DARK
            else ft.ThemeMode.LIGHT
        )
        is_dark = page.theme_mode == ft.ThemeMode.DARK
        icon = ft.icons.Icons.DARK_MODE if is_dark else ft.icons.Icons.LIGHT_MODE
        self._theme_btn_collapsed.icon = icon
        self._theme_btn_expanded.icon = icon
        page.update()

    def _toggle_search(self, e: ft.ControlEvent) -> None:
        self._search_input.visible = not self._search_input.visible
        if not self._search_input.visible:
            self._search_input.value = ""
            self._apply_search("")
        e.control.page.update()

    def _apply_search(self, query: str) -> None:
        self._search_query = query.strip().lower()
        self._rebuild_history_list()

    def _matches_search(self, entry) -> bool:
        if not self._search_query:
            return True
        haystack = " ".join([
            entry.text,
            entry.language,
            entry.formality,
            entry.model,
            entry.verdict,
            entry.feedback,
            entry.suggestion,
        ]).lower()
        return self._search_query in haystack

    def _rebuild_history_list(self) -> None:
        self._history_list.controls.clear()
        for original_idx, entry in enumerate(self._store.all()):
            if not self._matches_search(entry):
                continue
            preview = (entry.text[:60] + "…") if len(entry.text) > 60 else entry.text
            verdict = entry.verdict
            badge_color = ft.Colors.GREEN if verdict == "yes" else ft.Colors.RED
            badge = ft.Container(
                content=ft.Text(
                    verdict.upper() if verdict in ("yes", "no") else "ERR",
                    size=9,
                    color=ft.Colors.WHITE,
                ),
                bgcolor=badge_color,
                border_radius=3,
                padding=ft.padding.Padding(left=4, top=1, right=4, bottom=1),
            )
            item = ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text(
                            preview,
                            size=11,
                            max_lines=3,
                            overflow=ft.TextOverflow.ELLIPSIS,
                        ),
                        ft.Row(
                            controls=[
                                badge,
                                ft.Text(
                                    f"{entry.language} · {entry.formality}",
                                    size=9,
                                    color=ft.Colors.GREY,
                                ),
                            ],
                            spacing=4,
                        ),
                    ],
                    spacing=2,
                ),
                border=ft.Border.all(1, ft.Colors.OUTLINE),
                border_radius=5,
                padding=6,
                ink=True,
                on_click=lambda e, idx=original_idx: self._on_load(idx),
            )
            self._history_list.controls.append(item)
