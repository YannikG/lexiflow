"""Apply global UI theme from Theme preference."""

from __future__ import annotations

from typing import Literal

from lexiflow_core.config.settings import Theme
from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QApplication

from lexiflow_ui.theme_stylesheet import build_theme_stylesheet

EffectiveTheme = Literal["light", "dark"]


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
    try:
        scheme = app.styleHints().colorScheme()
        if scheme == Qt.ColorScheme.Dark:
            return "dark"
    except (AttributeError, TypeError):
        pass
    return "light"


def apply_app_theme(app: QApplication, *, theme: Theme) -> None:
    """Apply dark or light UI theme styling to the application."""
    effective = resolve_effective_theme(theme)
    app.setStyle("Fusion")
    app.setStyleSheet(build_theme_stylesheet(effective))
