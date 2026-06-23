"""Interactive practice panel with translation exercise flow."""

import flet as ft

from core.languages import DEFAULT_ENABLED_LANGUAGES


class PracticePanel:
    """Translation practice panel with phrase generation and checking."""

    def __init__(self):
        # --- Language dropdown ---
        self._lang_dropdown = ft.Dropdown(
            label="Language",
            width=150,
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
            width=220,
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

        # --- Generate controls ---
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
        self._generate_btn = ft.Button("Generate", icon="AUTO_AWESOME", width=130)
        self._generating_indicator = ft.ProgressRing(
            width=20, height=20, visible=False, stroke_width=2
        )

        # --- Source phrase display ---
        self._source_box = ft.Container(
            content=ft.Text(
                "Click Generate to get a phrase.",
                size=14,
                italic=True,
                color=ft.Colors.GREY,
            ),
            border=ft.Border.all(1, ft.Colors.OUTLINE),
            border_radius=5,
            padding=ft.padding.Padding(left=12, top=10, right=12, bottom=10),
            width=580,
        )

        # --- User translation input ---
        self._translation_input = ft.TextField(
            label="Your translation...",
            hint_text="Type your translation here...",
            multiline=True,
            min_lines=4,
            max_lines=8,
            width=580,
            text_size=14,
            border_color=ft.Colors.OUTLINE,
            focused_border_color=ft.Colors.PRIMARY,
            border_width=1.2,
            focused_border_width=1.8,
        )

        # --- Check/help buttons ---
        self._check_btn = ft.Button("Check", icon="CHECK", width=130)
        self._help_btn = ft.Button("Help", icon="LIGHTBULB_OUTLINE", width=130)
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
        self._output_box = ft.Container(
            content=self._output_column,
            width=580,
            height=140,
            visible=False,
            border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
            border_radius=5,
            padding=8,
        )

        self.view = ft.Column(
            controls=[
                ft.Text("Practice Mode", size=20, weight=ft.FontWeight.W_600),
                ft.Container(height=5),
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
                        self._generate_btn,
                        self._generating_indicator,
                    ],
                    alignment=ft.MainAxisAlignment.START,
                    spacing=15,
                ),
                ft.Container(height=10),
                ft.Text("Translate this phrase:", size=13, weight=ft.FontWeight.W_500),
                ft.Container(height=4),
                self._source_box,
                ft.Container(height=10),
                self._translation_input,
                ft.Container(height=10),
                ft.Row(
                    controls=[
                        self._check_btn,
                        self._help_btn,
                        self._check_indicator,
                    ],
                    alignment=ft.MainAxisAlignment.START,
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
    def selected_model(self) -> str:
        # Model selection now comes from Settings (global default).
        return ""

    # -- state --

    def set_generating(self, generating: bool) -> None:
        self._generating_indicator.visible = generating
        if generating:
            self._generate_btn.text = "Cancel"
            self._generate_btn.icon = "CLOSE"
        else:
            self._generate_btn.text = "Generate"
            self._generate_btn.icon = "AUTO_AWESOME"
            self._generate_btn.disabled = False

    def set_checking(self, checking: bool) -> None:
        self._check_indicator.visible = checking
        self._help_btn.disabled = checking
        if checking:
            self._check_btn.text = "Cancel"
            self._check_btn.icon = "CLOSE"
        else:
            self._check_btn.text = "Check"
            self._check_btn.icon = "CHECK"
            self._check_btn.disabled = False

    def set_languages(self, languages: list[str]) -> None:
        """Replace available languages and keep a valid selected value."""
        current = self._lang_dropdown.value
        self._lang_dropdown.options = [ft.dropdown.Option(lang, lang) for lang in languages]
        if current in languages:
            self._lang_dropdown.value = current
        elif languages:
            self._lang_dropdown.value = languages[0]
        else:
            self._lang_dropdown.value = None

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

    def set_source_phrase(self, phrase: str) -> None:
        self._source_box.content.value = phrase
        self._source_box.content.color = ft.Colors.ON_SURFACE
        self._source_box.content.italic = False
        self._translation_input.value = ""
        self.clear_output()

    def show_mistakes(self, mistakes: str) -> None:
        self._mistakes_text.value = mistakes
        self._mistakes_text.color = ft.Colors.RED_300
        self._output_box.visible = bool(mistakes or self._help_text.value)

    def show_help(self, translation: str) -> None:
        self._help_text.value = translation
        self._output_box.visible = bool(self._mistakes_text.value or translation)
