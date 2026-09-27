"""Responsive layout utilities for consistent breakpoints and mobile detection."""

import flet as ft


# ─── Breakpoints (px) ────────────────────────────────────────────────────────
# Based on common device widths:
# - Phone portrait:      ≤ 480
# - Phone landscape:     ≤ 820
# - Tablet portrait:     ≤ 820
# - Tablet landscape:    ≤ 1200
# - Desktop:             > 1200

BP_PHONE_MAX = 480
BP_TABLET_PORTRAIT_MAX = 820
BP_TABLET_LANDSCAPE_MAX = 1200


# ─── Viewport classification ─────────────────────────────────────────────────

class ViewportSize:
    """Viewport size categories."""
    PHONE = "phone"
    TABLET_PORTRAIT = "tablet_portrait"
    TABLET_LANDSCAPE = "tablet_landscape"
    DESKTOP = "desktop"


def classify_viewport(width: float, height: float) -> str:
    """Classify viewport into a size category."""
    if width <= 0 or height <= 0:
        return ViewportSize.DESKTOP

    is_portrait = height > width

    if width <= BP_PHONE_MAX:
        return ViewportSize.PHONE
    if width <= BP_TABLET_PORTRAIT_MAX and is_portrait:
        return ViewportSize.TABLET_PORTRAIT
    if width <= BP_TABLET_LANDSCAPE_MAX:
        return ViewportSize.TABLET_LANDSCAPE
    return ViewportSize.DESKTOP


def is_mobile_viewport(width: float, height: float) -> bool:
    """Return True if viewport should use mobile layout (stacked, drawer sidebar)."""
    viewport = classify_viewport(width, height)
    return viewport in (ViewportSize.PHONE, ViewportSize.TABLET_PORTRAIT)


def is_narrow_viewport(width: float) -> bool:
    """Return True if viewport is narrow enough to need stacked layouts."""
    return width <= BP_TABLET_PORTRAIT_MAX


def register_resize_handler(page: ft.Page, handler) -> None:
    """Add a resize listener without replacing listeners registered by other panels."""
    handlers = getattr(page, "_langadvisor_resize_handlers", None)
    if handlers is None:
        previous = page.on_resize
        handlers = []
        if previous is not None:
            handlers.append(previous)
        page._langadvisor_resize_handlers = handlers

        def dispatch(event: ft.PageResizeEvent) -> None:
            for callback in handlers:
                callback(event)
            page.update()

        page.on_resize = dispatch
    handlers.append(handler)


# ─── Responsive layout helpers ────────────────────────────────────────────────

def responsive_row(
    controls: list[ft.Control],
    *,
    spacing: int = 12,
    alignment: ft.MainAxisAlignment = ft.MainAxisAlignment.START,
    vertical_alignment: ft.CrossAxisAlignment = ft.CrossAxisAlignment.START,
    mobile_stacked: bool = True,
    expand: bool = True,
) -> ft.Control:
    """Create a Row that becomes a Column on mobile viewports.

    The returned control will automatically switch layout when the page resizes
    if you call `bind_responsive_layout(page, control)`.

    Args:
        controls: Controls to lay out
        spacing: Spacing between controls
        alignment: Main axis alignment
        vertical_alignment: Cross axis alignment (for Row)
        mobile_stacked: If True, stack vertically on mobile
        expand: Whether the container should expand
    """
    row = ft.Row(
        controls=controls,
        spacing=spacing,
        alignment=alignment,
        vertical_alignment=vertical_alignment,
        expand=expand,
    )
    column = ft.Column(
        controls=controls,
        spacing=spacing,
        alignment=alignment,
        horizontal_alignment=vertical_alignment,
        expand=expand,
    )

    # We'll store both layouts on a container that we'll swap
    container = ft.Container(content=row, expand=expand)
    container._responsive_row = row
    container._responsive_column = column
    container._mobile_stacked = mobile_stacked

    return container


def bind_responsive_layout(page: ft.Page, container: ft.Container) -> None:
    """Bind a container created with responsive_row to page resize events."""
    if not hasattr(container, '_responsive_row'):
        return

    def on_resize(e: ft.PageResizeEvent) -> None:
        mobile = is_mobile_viewport(e.width, e.height) if container._mobile_stacked else False
        container.content = container._responsive_column if mobile else container._responsive_row

    register_resize_handler(page, on_resize)
    # Initial layout
    mobile = is_mobile_viewport(page.width, page.height) if container._mobile_stacked else False
    container.content = container._responsive_column if mobile else container._responsive_row


def responsive_container(
    *,
    width_desktop: float | None = None,
    width_tablet: float | None = None,
    width_phone: float | None = None,
    expand: bool = False,
    **kwargs,
) -> ft.Container:
    """Create a container with responsive width.

    The container will adjust its width based on viewport size when bound
    with `bind_responsive_container`.

    Args:
        width_desktop: Width for desktop (> 1200px)
        width_tablet: Width for tablet (820-1200px)
        width_phone: Width for phone (< 820px)
        expand: Whether to expand
        **kwargs: Additional Container arguments
    """
    container = ft.Container(expand=expand, **kwargs)
    container._responsive_widths = {
        ViewportSize.DESKTOP: width_desktop,
        ViewportSize.TABLET_LANDSCAPE: width_tablet if width_tablet is not None else width_desktop,
        ViewportSize.TABLET_PORTRAIT: width_phone if width_phone is not None else width_tablet,
        ViewportSize.PHONE: width_phone,
    }
    return container


def bind_responsive_container(page: ft.Page, container: ft.Container) -> None:
    """Bind a responsive_container to page resize events."""
    if not hasattr(container, '_responsive_widths'):
        return

    def on_resize(e: ft.PageResizeEvent) -> None:
        viewport = classify_viewport(e.width, e.height)
        width = container._responsive_widths.get(viewport)
        if width is not None:
            container.width = width
        else:
            container.width = None

    register_resize_handler(page, on_resize)
    # Initial width
    viewport = classify_viewport(page.width, page.height)
    width = container._responsive_widths.get(viewport)
    if width is not None:
        container.width = width


def get_responsive_width(page: ft.Page, desktop: float, tablet: float = None, phone: float = None) -> float | None:
    """Get the appropriate width for the current viewport."""
    viewport = classify_viewport(page.width, page.height)
    if viewport == ViewportSize.DESKTOP:
        return desktop
    if viewport == ViewportSize.TABLET_LANDSCAPE:
        return tablet if tablet is not None else desktop
    if viewport == ViewportSize.TABLET_PORTRAIT:
        return phone if phone is not None else tablet
    return phone


# ─── Responsive control factories ────────────────────────────────────────────

def responsive_textfield(
    *,
    width_desktop: float = 580,
    width_tablet: float = None,
    width_phone: float = None,
    **kwargs,
) -> ft.TextField:
    """Create a TextField with responsive width."""
    return responsive_container(
        width_desktop=width_desktop,
        width_tablet=width_tablet,
        width_phone=width_phone,
        content=ft.TextField(**kwargs),
    )


def responsive_button_row(
    controls: list[ft.Control],
    *,
    spacing: int = 10,
    wrap: bool = True,
    **kwargs,
) -> ft.Row:
    """Create a button row that wraps on narrow screens."""
    return ft.Row(
        controls=controls,
        spacing=spacing,
        wrap=wrap,
        alignment=ft.MainAxisAlignment.START,
        **kwargs,
    )


# ─── Sidebar responsive behavior ──────────────────────────────────────────────

def should_collapse_sidebar(page: ft.Page) -> bool:
    """Determine if sidebar should be collapsed based on viewport."""
    return is_mobile_viewport(page.width, page.height)


class ResponsiveSidebarManager:
    """Manages sidebar collapse/expand based on viewport size."""

    def __init__(self, sidebar, page: ft.Page):
        self.sidebar = sidebar
        self.page = page
        self._was_collapsed = False
        register_resize_handler(page, self._on_resize)

    def _on_resize(self, e: ft.PageResizeEvent) -> None:
        should_collapse = should_collapse_sidebar(self.page)
        if should_collapse != self._was_collapsed:
            if should_collapse and not self.sidebar._collapsed.visible:
                self.sidebar.toggle()
            elif not should_collapse and self.sidebar._collapsed.visible:
                self.sidebar.toggle()
            self._was_collapsed = should_collapse
