"""Apply global UI theme from Theme preference."""

from __future__ import annotations

from typing import Literal

from lexiflow_core.config.settings import Theme
from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QApplication

EffectiveTheme = Literal["light", "dark"]

_DARK_MATERIAL_THEME = "dark_teal.xml"
_LIGHT_MATERIAL_THEME = "light_teal.xml"


def resolve_effective_theme(theme: Theme) -> EffectiveTheme:
    """Map Theme preference to effective light or dark UI theme."""
    if theme == "light":
        return "light"
    if theme == "dark":
        return "dark"
    return _resolve_system_effective_theme()


def _resolve_system_effective_theme() -> EffectiveTheme:
    app = QGuiApplication.instance()
    if app is None:
        return "light"
    scheme = app.styleHints().colorScheme()
    if scheme == Qt.ColorScheme.Dark:
        return "dark"
    return "light"


def _material_theme_file(effective: EffectiveTheme) -> str:
    if effective == "dark":
        return _DARK_MATERIAL_THEME
    return _LIGHT_MATERIAL_THEME


def apply_app_theme(app: QApplication, *, theme: Theme) -> None:
    """Apply global stylesheet for the given Theme preference."""
    from qt_material import apply_stylesheet

    effective = resolve_effective_theme(theme)
    material_theme = _material_theme_file(effective)
    invert_secondary = effective == "light"
    apply_stylesheet(
        app,
        theme=material_theme,
        invert_secondary=invert_secondary,
    )
