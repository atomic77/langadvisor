"""Lesson mode panel — multi-step practice round with batched grading."""

import flet as ft

from core.languages import DEFAULT_ENABLED_LANGUAGES
from ui.typography import clamp_font_scale, scale_control_fonts


class LessonPanel:
    """Lesson panel with five states: setup, generating, practicing, reviewing, results."""

    def __init__(self):
        self._font_scale = 1.0
        self._meta_label_width = 110

        # --- Language dropdown ---
        self._lang_dropdown = ft.Dropdown(
            label="Language",
            width=250,
            value="Serbian",
            options=[ft.dropdown.Option(lang, lang) for lang in DEFAULT_ENABLED_LANGUAGES],
        )

        # --- Formality dropdown ---
        self._formality_dropdown = ft.Dropdown(
            label="Formality",
            width=150,
            value="Colloquial",
            options=[
                ft.dropdown.Option("Colloquial", "Colloquial"),
                ft.dropdown.Option("Business", "Business"),
                ft.dropdown.Option("Formal", "Formal"),
            ],
        )

        # --- Category dropdown ---
        self._category_dropdown = ft.Dropdown(
            label="Category",
            width=350,
            value="Everyday Conversation",
            options=[
                ft.dropdown.Option("Everyday Conversation", "Everyday Conversation"),
                ft.dropdown.Option("Travel", "Travel"),
                ft.dropdown.Option("Food and Dining", "Food and Dining"),
                ft.dropdown.Option("Shopping", "Shopping"),
                ft.dropdown.Option("Work and Business", "Work and Business"),
                ft.dropdown.Option("School and Study", "School and Study"),
                ft.dropdown.Option("Health and Medical", "Health and Medical"),
                ft.dropdown.Option("Family and Relationships", "Family and Relationships"),
                ft.dropdown.Option("Technology", "Technology"),
                ft.dropdown.Option("News and Current Events", "News and Current Events"),
                ft.dropdown.Option("Culture and Entertainment", "Culture and Entertainment"),
                ft.dropdown.Option("Idioms and Expressions", "Idioms and Expressions"),
                ft.dropdown.Option("Formal Writing", "Formal Writing"),
                ft.dropdown.Option("Customer Service", "Customer Service"),
                ft.dropdown.Option("Emergencies", "Emergencies"),
            ],
        )

        # --- ECTS dropdown ---
        self._ects_dropdown = ft.Dropdown(
            label="ECTS Level",
            width=200,
            value="A1",
            options=[
                ft.dropdown.Option("A1", "A1 - Beginner"),
                ft.dropdown.Option("A2", "A2 - Elementary"),
                ft.dropdown.Option("B1", "B1 - Intermediate"),
                ft.dropdown.Option("B2", "B2 - Upper-Intermediate"),
                ft.dropdown.Option("C1", "C1 - Advanced"),
                ft.dropdown.Option("C2", "C2 - Proficient"),
            ],
        )

        # --- Round size dropdown ---
        self._round_size_dropdown = ft.Dropdown(
            label="Round size",
            width=130,
            value="10",
            options=[
                ft.dropdown.Option("5", "5"),
                ft.dropdown.Option("10", "10"),
                ft.dropdown.Option("20", "20"),
            ],
        )

        self._latinization_checkbox = ft.Checkbox(
            label="Latinization",
            value=False,
            tooltip="Show standard romanization for non-Latin scripts when available.",
        )

        # --- Start button + progress indicators ---
        self._start_btn = ft.Button(
            "Start Lesson", icon=ft.icons.Icons.PLAY_ARROW, width=170
        )
        self._generating_indicator = ft.ProgressRing(
            width=24, height=24, visible=False, stroke_width=2.5
        )
        self._grading_indicator = ft.ProgressRing(
            width=24, height=24, visible=False, stroke_width=2.5
        )

        # --- Header bar (always visible from SETUP and PRACTICING) ---
        self._header_bar = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            self._lang_dropdown,
                            self._formality_dropdown,
                            self._category_dropdown,
                        ],
                        alignment=ft.MainAxisAlignment.START,
                        spacing=15,
                        wrap=True,
                    ),
                    ft.Row(
                        controls=[
                            self._ects_dropdown,
                            self._round_size_dropdown,
                            self._latinization_checkbox,
                            self._start_btn,
                            self._generating_indicator,
                        ],
                        alignment=ft.MainAxisAlignment.START,
                        spacing=15,
                    ),
                ],
                spacing=8,
            ),
            padding=ft.padding.Padding(left=4, top=4, right=4, bottom=4),
        )

        # --- Progress text (visible only during PRACTICING) ---
        self._progress_text = ft.Text(
            value="", size=13, weight=ft.FontWeight.W_500, visible=False
        )
        self._progress_bar = ft.ProgressBar(
            value=0, width=400, visible=False, bar_height=4
        )

        # --- SETUP body ---
        self._setup_body = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Container(height=10),
                    ft.Text(
                        "Lesson Mode",
                        size=22,
                        weight=ft.FontWeight.W_600,
                    ),
                    ft.Container(height=4),
                    ft.Text(
                        "A multi-step translation practice round.\n"
                        "Choose your settings above and click Start Lesson to generate "
                        "a fresh set of phrases. You'll translate each one, then receive "
                        "a graded review of all your answers at the end.",
                        size=13,
                        color=ft.Colors.GREY,
                    ),
                ],
                spacing=6,
            ),
            visible=True,
        )

        # --- GENERATING body ---
        self._generating_body = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Container(height=40),
                    ft.Row(
                        controls=[
                            self._generating_indicator,
                            ft.Text("Generating phrases…", size=14),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=12,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=12,
            ),
            visible=False,
            expand=True,
        )

        # --- PRACTICING body ---
        self._phrase_text = ft.Text(
            value="", size=22, weight=ft.FontWeight.W_500, selectable=True
        )
        self._phrase_card = ft.Container(
            content=self._phrase_text,
            border=ft.Border.all(1, ft.Colors.OUTLINE),
            border_radius=8,
            padding=ft.padding.Padding(left=20, top=18, right=20, bottom=18),
            bgcolor=ft.Colors.SURFACE_CONTAINER_LOWEST,
            width=800,
        )
        self._romanization_text = ft.Text(
            value="", size=17, selectable=True, color=ft.Colors.BLUE_200
        )
        self._romanization_card = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        "Latinization",
                        size=11,
                        weight=ft.FontWeight.W_700,
                        color=ft.Colors.GREY,
                    ),
                    self._romanization_text,
                ],
                spacing=4,
            ),
            border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
            border_radius=8,
            padding=ft.padding.Padding(left=16, top=12, right=16, bottom=12),
            bgcolor=ft.Colors.SURFACE_CONTAINER_LOW,
            width=800,
            visible=False,
        )
        self._answer_input = ft.TextField(
            label="Your translation…",
            hint_text="Type your English translation here…",
            multiline=True,
            min_lines=6,
            max_lines=12,
            text_size=16,
            border_color=ft.Colors.OUTLINE,
            focused_border_color=ft.Colors.PRIMARY,
            border_width=1.2,
            focused_border_width=1.8,
            width=800,
        )
        self._reference_translation = ""
        self._reference_text = ft.Text(
            value="",
            size=14,
            selectable=True,
            color=ft.Colors.BLUE_200,
        )
        self._reference_card = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        "Translation",
                        size=11,
                        weight=ft.FontWeight.W_700,
                        color=ft.Colors.GREY,
                    ),
                    self._reference_text,
                ],
                spacing=4,
            ),
            border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
            border_radius=8,
            padding=ft.padding.Padding(left=16, top=12, right=16, bottom=12),
            bgcolor=ft.Colors.SURFACE_CONTAINER_LOW,
            width=800,
            visible=False,
        )
        self._prev_btn = ft.Button(
            "Previous", icon=ft.icons.Icons.ARROW_BACK, width=140
        )
        self._next_btn = ft.Button(
            "Next", icon=ft.icons.Icons.ARROW_FORWARD, width=140
        )
        self._help_btn = ft.Button(
            "Show Translation", icon=ft.icons.Icons.TRANSLATE, width=180
        )
        self._skip_btn = ft.OutlinedButton("Skip", width=110)
        self._submit_btn = ft.Button(
            "Submit Round", icon=ft.icons.Icons.CHECK, width=170
        )
        self._practicing_body = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Container(height=8),
                    self._progress_text,
                    self._progress_bar,
                    ft.Container(height=8),
                    self._phrase_card,
                    self._romanization_card,
                    ft.Container(height=14),
                    self._answer_input,
                    self._reference_card,
                    ft.Container(height=14),
                    ft.Row(
                        controls=[
                            self._prev_btn,
                            self._next_btn,
                            self._help_btn,
                            self._skip_btn,
                            self._submit_btn,
                        ],
                        alignment=ft.MainAxisAlignment.START,
                        spacing=10,
                    ),
                ],
                spacing=4,
            ),
            visible=False,
            expand=True,
        )

        # --- REVIEWING body ---
        self._reviewing_body = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Container(height=40),
                    ft.Row(
                        controls=[
                            self._grading_indicator,
                            ft.Text("Grading your answers…", size=14),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=12,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=12,
            ),
            visible=False,
            expand=True,
        )

        # --- RESULTS body ---
        self._score_text = ft.Text(
            value="", size=24, weight=ft.FontWeight.W_700, selectable=True
        )
        self._summary_text = ft.Text(
            value="", size=13, selectable=True, color=ft.Colors.GREY
        )
        self._score_banner = ft.Container(
            content=ft.Column(
                controls=[self._score_text, self._summary_text],
                spacing=6,
            ),
            border=ft.Border.all(1, ft.Colors.OUTLINE),
            border_radius=8,
            padding=ft.padding.Padding(left=16, top=14, right=16, bottom=14),
            visible=False,
        )
        self._results_list = ft.ListView(
            controls=[], expand=True, spacing=10, padding=5
        )
        self._reset_btn = ft.Button(
            "New Round", icon=ft.icons.Icons.REFRESH, width=160
        )
        self._results_body = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Container(height=4),
                    self._score_banner,
                    ft.Container(height=8),
                    self._results_list,
                    ft.Container(height=8),
                    ft.Row(
                        controls=[self._reset_btn],
                        alignment=ft.MainAxisAlignment.START,
                    ),
                ],
                spacing=4,
            ),
            visible=False,
            expand=True,
        )

        # --- Status text (errors) ---
        self._status_text = ft.Text(
            value="", size=12, color=ft.Colors.ORANGE, visible=False
        )

        self.view = ft.Column(
            controls=[
                self._header_bar,
                ft.Container(height=6),
                self._setup_body,
                self._generating_body,
                self._practicing_body,
                self._reviewing_body,
                self._results_body,
                self._status_text,
            ],
            expand=True,
            spacing=4,
            scroll=ft.ScrollMode.AUTO,
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
    def round_size(self) -> int:
        try:
            return int(self._round_size_dropdown.value or "10")
        except (ValueError, TypeError):
            return 10

    @property
    def latinization_enabled(self) -> bool:
        return bool(self._latinization_checkbox.value)

    # -- state setters --

    def set_languages(self, languages: list[str]) -> None:
        """Replace available languages and keep a valid selected value."""
        current = self._lang_dropdown.value
        self._lang_dropdown.options = [
            ft.dropdown.Option(lang, lang) for lang in languages
        ]
        if current in languages:
            self._lang_dropdown.value = current
        elif languages:
            self._lang_dropdown.value = languages[0]
        else:
            self._lang_dropdown.value = None

    def apply_typography(self, scale: float) -> None:
        self._font_scale = clamp_font_scale(scale)
        self._meta_label_width = int(110 + (self._font_scale - 1.0) * 70)
        self._phrase_card.width = int(800 + (self._font_scale - 1.0) * 120)
        self._romanization_card.width = int(800 + (self._font_scale - 1.0) * 120)
        self._reference_card.width = int(800 + (self._font_scale - 1.0) * 120)
        self._answer_input.width = int(800 + (self._font_scale - 1.0) * 120)
        scale_control_fonts(self.view, self._font_scale)

    def set_status(self, text: str, is_error: bool = False) -> None:
        self._status_text.value = text
        self._status_text.color = ft.Colors.ORANGE if is_error else ft.Colors.GREY
        self._status_text.visible = bool(text)

    def _set_busy(self, generating: bool) -> None:
        """Toggle the generating indicator and Start-button label."""
        self._generating_indicator.visible = generating
        if generating:
            self._start_btn.text = "Cancel"
            self._start_btn.icon = ft.icons.Icons.CLOSE
            self._round_size_dropdown.disabled = True
            self._latinization_checkbox.disabled = True
        else:
            self._start_btn.text = "Start Lesson"
            self._start_btn.icon = ft.icons.Icons.PLAY_ARROW
            self._start_btn.disabled = False
            self._round_size_dropdown.disabled = False
            self._latinization_checkbox.disabled = False

    def show_setup(self) -> None:
        self._setup_body.visible = True
        self._generating_body.visible = False
        self._practicing_body.visible = False
        self._reviewing_body.visible = False
        self._results_body.visible = False
        self._progress_text.visible = False
        self._progress_bar.visible = False
        self._score_banner.visible = False
        self._generating_indicator.visible = False
        self._grading_indicator.visible = False
        self._set_busy(False)
        self.set_status("")

    def show_generating(self) -> None:
        self._setup_body.visible = False
        self._generating_body.visible = True
        self._practicing_body.visible = False
        self._reviewing_body.visible = False
        self._results_body.visible = False
        self._progress_text.visible = False
        self._progress_bar.visible = False
        self._score_banner.visible = False
        self._set_busy(True)

    def show_practicing(
        self,
        current: int,
        total: int,
        phrase: str,
        answer: str = "",
        romanization: str = "",
        reference_translation: str = "",
    ) -> None:
        self._setup_body.visible = False
        self._generating_body.visible = False
        self._practicing_body.visible = True
        self._reviewing_body.visible = False
        self._results_body.visible = False
        self._score_banner.visible = False
        self._set_busy(False)
        self._progress_text.value = f"Step {current + 1} of {total}"
        self._progress_text.visible = True
        self._progress_bar.value = current / max(total, 1)
        self._progress_bar.visible = True
        self._phrase_text.value = phrase
        self._romanization_text.value = romanization
        self._romanization_card.visible = bool(romanization.strip())
        self._answer_input.value = answer
        self._reference_translation = reference_translation.strip()
        self._reference_text.value = ""
        self._reference_card.visible = False
        is_last = current >= total - 1
        self._next_btn.visible = not is_last
        self._submit_btn.visible = is_last
        self._next_btn.disabled = False
        self._submit_btn.disabled = False
        self._prev_btn.disabled = current <= 0
        self._help_btn.disabled = not bool(self._reference_translation)
        self._skip_btn.disabled = is_last and bool(answer.strip())

    def show_reference_translation(self, translation: str | None = None) -> None:
        text = (
            translation if translation is not None else self._reference_translation
        ).strip()
        self._reference_translation = text
        self._reference_text.value = text
        self._reference_card.visible = bool(text)

    def show_reviewing(self) -> None:
        self._setup_body.visible = False
        self._generating_body.visible = False
        self._practicing_body.visible = False
        self._reviewing_body.visible = True
        self._results_body.visible = False
        self._progress_text.visible = False
        self._progress_bar.visible = False
        self._score_banner.visible = False
        self._generating_indicator.visible = False
        self._grading_indicator.visible = True
        self._set_busy(False)
        # Disable navigation buttons while grading.
        self._prev_btn.disabled = True
        self._next_btn.disabled = True
        self._help_btn.disabled = True
        self._skip_btn.disabled = True
        self._submit_btn.disabled = True

    def show_results(
        self,
        results: list[dict],
        summary: str,
        score_total: int,
        score_max: int,
    ) -> None:
        self._setup_body.visible = False
        self._generating_body.visible = False
        self._practicing_body.visible = False
        self._reviewing_body.visible = False
        self._results_body.visible = True
        self._grading_indicator.visible = False
        self._progress_text.visible = False
        self._progress_bar.visible = False
        self._set_busy(False)

        # Score banner — color-coded by percentage.
        if score_max > 0:
            pct = score_total / score_max
        else:
            pct = 0
        if pct >= 0.8:
            banner_color = ft.Colors.GREEN_400
        elif pct >= 0.5:
            banner_color = ft.Colors.ORANGE_400
        else:
            banner_color = ft.Colors.RED_400
        self._score_text.value = (
            f"{score_total} / {score_max}   ({int(pct * 100)}%)"
        )
        self._score_text.color = banner_color
        self._summary_text.value = summary or "(No overall summary provided.)"
        self._score_banner.border = ft.Border.all(1, banner_color)
        self._score_banner.visible = True

        # Result cards.
        self._results_list.controls = [
            self._build_result_card(idx, r) for idx, r in enumerate(results, start=1)
        ]
        self.apply_typography(self._font_scale)

    def _build_result_card(self, idx: int, r: dict) -> ft.Container:
        score = r.get("score", 0)
        if score >= 8:
            badge_color = ft.Colors.GREEN_400
        elif score >= 5:
            badge_color = ft.Colors.ORANGE_400
        else:
            badge_color = ft.Colors.RED_400
        badge = ft.Container(
            content=ft.Text(
                f"{score}/10", size=11, color=ft.Colors.WHITE, weight=ft.FontWeight.W_700
            ),
            bgcolor=badge_color,
            border_radius=3,
            padding=ft.padding.Padding(left=6, top=2, right=6, bottom=2),
        )
        controls = [
            ft.Row(
                controls=[
                    ft.Text(f"{idx}.", size=13, weight=ft.FontWeight.W_700),
                    ft.Text(
                        r.get("phrase", ""),
                        size=14,
                        weight=ft.FontWeight.W_600,
                        selectable=True,
                        expand=True,
                    ),
                    badge,
                ],
                spacing=10,
                vertical_alignment=ft.CrossAxisAlignment.START,
            ),
            ft.Container(height=6),
        ]
        romanization = (r.get("romanization") or "").strip()
        if romanization:
            controls.append(
                ft.Row(
                    controls=[
                        ft.Container(
                            content=ft.Text(
                                "Latinization:", size=11, weight=ft.FontWeight.W_600
                            ),
                            width=self._meta_label_width,
                        ),
                        ft.Text(
                            romanization,
                            size=13,
                            selectable=True,
                            color=ft.Colors.BLUE_200,
                            expand=True,
                        ),
                    ],
                    spacing=6,
                )
            )
        controls.extend(
            [
                ft.Row(
                    controls=[
                        ft.Container(
                            content=ft.Text(
                                "Your answer:", size=11, weight=ft.FontWeight.W_600
                            ),
                            width=self._meta_label_width,
                        ),
                        ft.Text(
                            r.get("user_answer", "") or "(skipped)",
                            size=13,
                            selectable=True,
                            color=ft.Colors.GREY,
                            expand=True,
                        ),
                    ],
                    spacing=6,
                ),
                ft.Row(
                    controls=[
                        ft.Container(
                            content=ft.Text(
                                "Reference:", size=11, weight=ft.FontWeight.W_600
                            ),
                            width=self._meta_label_width,
                        ),
                        ft.Text(
                            r.get("reference", "") or "(no reference)",
                            size=13,
                            selectable=True,
                            expand=True,
                        ),
                    ],
                    spacing=6,
                ),
                ft.Row(
                    controls=[
                        ft.Container(
                            content=ft.Text(
                                "Better:", size=11, weight=ft.FontWeight.W_600
                            ),
                            width=self._meta_label_width,
                        ),
                        ft.Text(
                            r.get("better", "") or "(none suggested)",
                            size=13,
                            selectable=True,
                            color=ft.Colors.BLUE_200,
                            expand=True,
                        ),
                    ],
                    spacing=6,
                ),
                ft.Row(
                    controls=[
                        ft.Container(
                            content=ft.Text(
                                "Mistakes:", size=11, weight=ft.FontWeight.W_600
                            ),
                            width=self._meta_label_width,
                        ),
                        ft.Text(
                            r.get("mistakes", "") or "(none noted)",
                            size=13,
                            selectable=True,
                            color=ft.Colors.RED_200,
                            expand=True,
                        ),
                    ],
                    spacing=6,
                ),
            ]
        )
        return ft.Container(
            content=ft.Column(controls=controls, spacing=2),
            border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
            border_radius=8,
            padding=ft.padding.Padding(left=14, top=12, right=14, bottom=12),
        )

    # -- practicing input accessor --

    @property
    def current_answer(self) -> str:
        return self._answer_input.value or ""