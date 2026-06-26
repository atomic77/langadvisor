"""Typography helpers for app-wide accessibility settings."""

from __future__ import annotations

from numbers import Real

import flet as ft

MIN_SCALED_FONT = 9
FONT_SCALE_MIN = 0.9
FONT_SCALE_MAX = 1.6


def clamp_font_scale(scale: float) -> float:
    """Clamp font scale to supported accessibility bounds."""
    return max(FONT_SCALE_MIN, min(FONT_SCALE_MAX, float(scale)))


def scale_control_fonts(control: ft.Control | None, scale: float) -> None:
    """Apply text/icon scaling recursively while preserving each control's baseline size."""
    if control is None:
        return

    scale = clamp_font_scale(scale)
    _scale_single_control(control, scale)

    for child in _iter_children(control):
        scale_control_fonts(child, scale)


def _scale_single_control(control: ft.Control, scale: float) -> None:
    for attr in ("size", "text_size", "icon_size"):
        if not hasattr(control, attr):
            continue

        value = getattr(control, attr)
        if not isinstance(value, Real):
            continue

        baseline_attr = f"_baseline_{attr}"
        baseline = getattr(control, baseline_attr, None)
        if baseline is None:
            baseline = float(value)
            setattr(control, baseline_attr, baseline)

        scaled = max(MIN_SCALED_FONT, round(float(baseline) * scale, 1))
        setattr(control, attr, scaled)


def _iter_children(control: ft.Control) -> list[ft.Control]:
    children: list[ft.Control] = []
    for attr in (
        "content",
        "controls",
        "actions",
        "title",
        "subtitle",
        "label",
        "leading",
        "trailing",
    ):
        if not hasattr(control, attr):
            continue
        value = getattr(control, attr)
        if isinstance(value, ft.Control):
            children.append(value)
            continue
        if isinstance(value, list):
            children.extend(item for item in value if isinstance(item, ft.Control))
    return children
