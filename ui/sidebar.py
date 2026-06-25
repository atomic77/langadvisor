"""Sidebar widget with history list."""

import flet as ft

from core.history_store import HistoryStore


class Sidebar:
    """Collapsible sidebar containing navigation, search, and history."""

    def __init__(
        self,
        store: HistoryStore,
        on_new: callable,
        on_load: callable,
        on_mode_change: callable = None,
    ):
        self._store = store
        self._on_new = on_new
        self._on_load = on_load
        self._on_mode_change = on_mode_change
        self._store.on_change(self._rebuild_history_list)
        self._search_query = ""
        self._mode = "grammar"  # "grammar", "practice", or "settings"

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
                    ft.IconButton(
                        icon=ft.icons.Icons.SCHOOL,
                        icon_size=22,
                        tooltip="Practice",
                        on_click=lambda e: self._set_mode("practice"),
                    ),
                    ft.IconButton(
                        icon=ft.icons.Icons.SETTINGS,
                        icon_size=22,
                        tooltip="Settings",
                        on_click=lambda e: self._set_mode("settings"),
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
            visible=False,
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
            on_click=lambda e: self._set_mode("grammar") or self._on_new(),
        )
        self._practice_link = ft.TextButton(
            content=ft.Row(
                [ft.Icon(ft.icons.Icons.SCHOOL, size=16), ft.Text("Practice", size=13)]
            ),
            on_click=lambda e: self._set_mode("practice"),
        )
        self._settings_link = ft.TextButton(
            content=ft.Row(
                [ft.Icon(ft.icons.Icons.SETTINGS, size=16), ft.Text("Settings", size=13)]
            ),
            on_click=lambda e: self._set_mode("settings"),
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
            border_color=ft.Colors.OUTLINE,
            focused_border_color=ft.Colors.PRIMARY,
            border_width=1.2,
            focused_border_width=1.8,
        )
        divider = ft.Divider(height=1, color=ft.Colors.OUTLINE_VARIANT)
        self._history_header = ft.Text("History", size=13, weight=ft.FontWeight.W_600)
        self._clear_history_btn = ft.IconButton(
            icon=ft.icons.Icons.DELETE_OUTLINE,
            icon_size=16,
            tooltip="Clear history",
            on_click=lambda e: self._clear_history(e),
            disabled=True,
        )
        self._history_header_row = ft.Row(
            controls=[
                self._history_header,
                self._clear_history_btn,
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        self._practice_stats = ft.Column(
            controls=[
                ft.Text("🔥 Streak: 0", size=12),
                ft.Text("Session: 0 correct", size=11, color=ft.Colors.GREY),
                ft.Text("Total completed: 0", size=11, color=ft.Colors.GREY),
            ],
            spacing=4,
            visible=False,
        )
        self._practice_topics = ft.Column(
            controls=[
                self._make_topic_btn("Grammar Rules", "📝"),
                self._make_topic_btn("Verb Tenses", "🔄"),
                self._make_topic_btn("Prepositions", "📍"),
                self._make_topic_btn("Articles", "🔤"),
            ],
            spacing=6,
            visible=False,
        )

        self._expanded = ft.Container(
            content=ft.Column(
                controls=[
                    header,
                    new_btn,
                    self._practice_link,
                    self._settings_link,
                    search_btn,
                    self._search_input,
                    divider,
                    self._history_header_row,
                    self._practice_stats,
                    self._practice_topics,
                    self._history_list,
                ],
                spacing=6,
            ),
            width=220,
            bgcolor=ft.Colors.SURFACE_CONTAINER_LOW,
            border_radius=8,
            padding=10,
            visible=True,
        )

        self.view = ft.Row(
            controls=[self._collapsed, self._expanded],
            spacing=0,
            vertical_alignment=ft.CrossAxisAlignment.START,
        )

        self._rebuild_history_list()

    def _make_topic_btn(self, label: str, emoji: str) -> ft.Container:
        return ft.Container(
            content=ft.Text(f"{emoji}  {label}", size=12),
            border=ft.Border.all(1, ft.Colors.OUTLINE),
            border_radius=5,
            padding=ft.padding.Padding(left=8, top=6, right=8, bottom=6),
            ink=True,
        )

    def _set_mode(self, mode: str) -> None:
        """Switch between 'grammar', 'practice', and 'settings' mode."""
        if self._mode == mode:
            return
        self._mode = mode
        self._update_contextual_content()
        if self._on_mode_change:
            self._on_mode_change(mode)

    def _update_contextual_content(self) -> None:
        """Show contextual sidebar content for the active mode."""
        if self._mode == "practice":
            self._history_header.value = "Practice"
            self._clear_history_btn.visible = False
            self._history_list.visible = False
            self._practice_stats.visible = False
            self._practice_topics.visible = False
            self._search_input.visible = False
        elif self._mode == "settings":
            self._history_header.value = "Settings"
            self._clear_history_btn.visible = False
            self._history_list.visible = False
            self._practice_stats.visible = False
            self._practice_topics.visible = False
            self._search_input.visible = False
        else:
            self._history_header.value = "History"
            self._clear_history_btn.visible = True
            self._history_list.visible = True
            self._practice_stats.visible = False
            self._practice_topics.visible = False
            self._search_input.visible = False

    def toggle(self) -> None:
        expanded = self._expanded.visible
        self._collapsed.visible = expanded
        self._expanded.visible = not expanded

    def _toggle_theme(self, e: ft.ControlEvent) -> None:
        page = e.control.page
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

    def _clear_history(self, e: ft.ControlEvent) -> None:
        self._search_query = ""
        self._search_input.value = ""
        self._store.clear()
        e.control.page.update()

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
        entries = self._store.all()
        self._clear_history_btn.disabled = not entries
        for original_idx, entry in enumerate(entries):
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
