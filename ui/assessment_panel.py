"""Main assessment input and results panel."""

import flet as ft


class AssessmentPanel:
    """Encapsulates the text input, controls, and result displays."""

    def __init__(self, on_assess_click, on_text_change, on_keyboard):
        self._lang_dropdown = ft.Dropdown(
            label="Language",
            width=150,
            value="Serbian",
            options=[
                ft.dropdown.Option("English", "English"),
                ft.dropdown.Option("Serbian", "Serbian"),
                ft.dropdown.Option("Italian", "Italian"),
                ft.dropdown.Option("French", "French"),
                ft.dropdown.Option("Japanese", "Japanese"),
            ],
        )
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
        self._model_status = ft.Text(
            value="Loading models…", size=11, color=ft.Colors.GREY
        )
        self._model_dropdown = ft.Dropdown(label="Model", width=250)
        self._assess_btn = ft.Button("Assess", icon="CHECK", width=130)
        self._assessing_indicator = ft.ProgressRing(
            width=20, height=20, visible=False, stroke_width=2
        )

        self._grammar_result = ft.Text(
            value="", size=15, visible=False, weight=ft.FontWeight.W_500
        )
        self._feedback_text = ft.Text(value="", size=13, selectable=True)
        self._feedback_box = ft.Container(
            content=ft.Column(controls=[self._feedback_text], scroll=ft.ScrollMode.AUTO),
            width=580,
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
            width=580,
            read_only=True,
            visible=False,
            border_color=ft.Colors.GREEN_200,
            focused_border_color=ft.Colors.GREEN_400,
        )

        self._txt_input = ft.TextField(
            label="Write your text here…",
            hint_text="Type or paste text to assess, then click Assess (or press Ctrl+Enter)…",
            multiline=True,
            min_lines=10,
            max_lines=20,
            width=580,
            text_size=14,
            on_change=on_text_change,
        )

        self._assess_btn.on_click = on_assess_click

        self.view = ft.Column(
            controls=[
                self._txt_input,
                ft.Row(
                    controls=[self._lang_dropdown, self._formality_dropdown],
                    alignment=ft.MainAxisAlignment.START,
                    width=580,
                    spacing=15,
                ),
                ft.Row(
                    controls=[
                        self._model_dropdown,
                        self._model_status,
                        self._assess_btn,
                        self._assessing_indicator,
                    ],
                    alignment=ft.MainAxisAlignment.START,
                    width=580,
                    spacing=15,
                ),
                self._grammar_result,
                self._feedback_box,
                self._suggestion_box,
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

    @property
    def selected_model(self) -> str:
        return self._model_dropdown.value or ""

    @selected_model.setter
    def selected_model(self, value: str) -> None:
        self._model_dropdown.value = value

    # -- model status --

    def set_model_status(self, message: str, is_error: bool = False) -> None:
        self._model_status.value = message
        self._model_status.color = ft.Colors.RED if is_error else ft.Colors.GREY

    def hide_model_status(self) -> None:
        self._model_status.visible = False

    def set_models(self, names: list[str]) -> None:
        self._model_dropdown.options = [ft.dropdown.Option(n) for n in names]
        if names:
            self._model_dropdown.value = names[0]

    # -- assessment state --

    def set_assessing(self, assessing: bool) -> None:
        self._assessing_indicator.visible = assessing
        if assessing:
            self._assess_btn.text = "Cancel"
            self._assess_btn.icon = "CLOSE"
        else:
            self._assess_btn.text = "Assess"
            self._assess_btn.icon = "CHECK"
            self._assess_btn.disabled = False

    def disable_assess_button(self) -> None:
        self._assess_btn.disabled = True

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
