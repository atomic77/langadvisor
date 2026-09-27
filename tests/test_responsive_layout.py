"""Regression checks for narrow Lesson and Translation layouts."""

from types import SimpleNamespace

from ui.lesson_panel import LessonPanel
from ui.translation_panel import TranslationPanel


class PageStub:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.on_resize = None
        self.updates = 0

    def update(self):
        self.updates += 1

    def resize(self, width: int, height: int):
        self.width = width
        self.height = height
        self.on_resize(SimpleNamespace(width=width, height=height))


def test_lesson_setup_wraps_and_shrinks_on_phone():
    page = PageStub(390, 844)
    panel = LessonPanel()
    panel.bind_page(page)

    setup_rows = panel._header_bar.content.controls
    assert all(row.wrap for row in setup_rows)
    assert panel._category_dropdown.width <= 260

    page.resize(320, 700)
    assert panel._ects_dropdown.width <= 180
    assert panel._start_btn in setup_rows[1].controls


def test_translation_stacks_and_remains_scrollable_after_resize():
    page = PageStub(1200, 800)
    panel = TranslationPanel()
    panel.bind_page(page)
    assert panel.view.content is panel._root_row

    page.resize(390, 844)
    assert panel.view.content is panel._root_column
    assert panel._left_column.width is None
    assert panel._results_box.height == 260
    assert panel._root_column.scroll is not None

    page.resize(1200, 800)
    assert panel.view.content is panel._root_row


def test_panel_resize_handlers_coexist():
    page = PageStub(1200, 800)
    lesson = LessonPanel()
    translation = TranslationPanel()
    lesson.bind_page(page)
    translation.bind_page(page)

    page.resize(390, 844)
    assert lesson._category_dropdown.width <= 260
    assert translation.view.content is translation._root_column
    assert page.updates == 1
