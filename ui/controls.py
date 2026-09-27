"""Shared Flet dropdown factories and option lists used across panels.

Centralizing these here means adding a formality level, practice category, or
CEFR level is a one-file edit instead of a change copied into every panel.
"""

import flet as ft

FORMALITY_OPTIONS = ["Colloquial", "Business", "Formal"]

CATEGORY_OPTIONS = [
    "Everyday Conversation",
    "Travel",
    "Food and Dining",
    "Shopping",
    "Work and Business",
    "School and Study",
    "Health and Medical",
    "Family and Relationships",
    "Technology",
    "News and Current Events",
    "Culture and Entertainment",
    "Idioms and Expressions",
    "Formal Writing",
    "Customer Service",
    "Emergencies",
]

# (key, display label) pairs — the key is what flows into LLM prompts.
ECTS_LEVEL_OPTIONS = [
    ("A1", "A1 - Beginner"),
    ("A2", "A2 - Elementary"),
    ("B1", "B1 - Intermediate"),
    ("B2", "B2 - Upper-Intermediate"),
    ("C1", "C1 - Advanced"),
    ("C2", "C2 - Proficient"),
]


def _options(items) -> list[ft.dropdown.Option]:
    """Build dropdown options from plain strings or (key, label) pairs."""
    return [
        ft.dropdown.Option(item, item)
        if isinstance(item, str)
        else ft.dropdown.Option(item[0], item[1])
        for item in items
    ]


def language_dropdown(languages, *, width, value=None) -> ft.Dropdown:
    dd = ft.Dropdown(label="Language", width=width, options=_options(languages))
    dd.value = value if value is not None else (languages[0] if languages else None)
    return dd


def formality_dropdown(*, width=150, value="Colloquial") -> ft.Dropdown:
    return ft.Dropdown(
        label="Formality", width=width, value=value, options=_options(FORMALITY_OPTIONS)
    )


def category_dropdown(*, width=350, value="Everyday Conversation") -> ft.Dropdown:
    return ft.Dropdown(
        label="Category", width=width, value=value, options=_options(CATEGORY_OPTIONS)
    )


def ects_dropdown(*, width=250, value="A1") -> ft.Dropdown:
    return ft.Dropdown(
        label="ECTS Level", width=width, value=value, options=_options(ECTS_LEVEL_OPTIONS)
    )


def set_dropdown_languages(dropdown: ft.Dropdown, languages: list[str]) -> None:
    """Replace a language dropdown's options, keeping a valid selected value.

    If the current selection is no longer available, fall back to the first
    language (or None when the list is empty).
    """
    current = dropdown.value
    dropdown.options = _options(languages)
    if current in languages:
        dropdown.value = current
    elif languages:
        dropdown.value = languages[0]
    else:
        dropdown.value = None