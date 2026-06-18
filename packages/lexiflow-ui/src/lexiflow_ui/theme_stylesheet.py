"""Build and apply Qt stylesheets from bundled dark/light theme color tokens."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal

from lexiflow_core.config.settings import Theme
from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QApplication

EffectiveTheme = Literal["light", "dark"]

_THEMES_DIR = Path(__file__).resolve().parent / "themes"
_TOKEN_FILES: dict[EffectiveTheme, str] = {
    "dark": "dark_theme.json",
    "light": "light_theme.json",
}
_APP_QSS = _THEMES_DIR / "app.qss"

TAB_PUSH_BUTTON_IDS = (
    "reader_tab_native",
    "reader_tab_translated",
    "add_text_tab_native",
    "add_text_tab_target",
)

_TAB_SELECTORS = tuple(
    f"QPushButton#{object_name}" for object_name in TAB_PUSH_BUTTON_IDS
) + ('QPushButton[objectName^="reader_tab_simplified_"]',)

_SECONDARY_BUTTONS = (
    "QPushButton#reader_edit_button",
    "QPushButton#reader_delete_button",
    "QPushButton#reader_cancel_button",
    "QPushButton#sidebar_add_text_button",
    "QPushButton#empty_state_action",
    "QPushButton#trash_empty_button",
    "QPushButton#trash_close_button",
    "QPushButton#jobs_panel_close_button",
    "QPushButton#reader_retranslate_button",
    "QPushButton#reader_resimplify_button",
    "QPushButton#reader_delete_simplification_button",
    "QPushButton#switch_language_add_button",
    "QPushButton#switch_language_cancel_button",
    "QPushButton#settings_change_native_language",
    "QPushButton#settings_test_ollama",
    "QPushButton#settings_hf_token_link",
    "QPushButton#settings_check_updates",
    "QPushButton#settings_download_updates",
    "QPushButton#settings_redownload_native-llm",
    "QPushButton#settings_redownload_native-embedding",
    "QPushButton#settings_redownload_all",
    "QPushButton#settings_reset_button",
    "QPushButton#settings_cancel_button",
)


def _tab_selectors(*, pseudo: str | None = None) -> str:
    if pseudo is None:
        return ",\n".join(_TAB_SELECTORS)
    return ",\n".join(f"{selector}:{pseudo}" for selector in _TAB_SELECTORS)


def load_theme_colors(effective: EffectiveTheme) -> dict[str, str]:
    """Load theme color tokens shipped with lexiflow-ui."""
    path = _THEMES_DIR / _TOKEN_FILES[effective]
    raw: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    return {key: str(value) for key, value in raw.items()}


def _color(colors: dict[str, str], key: str, *, fallback: str | None = None) -> str:
    if key in colors:
        return colors[key]
    if fallback is not None:
        return fallback
    raise KeyError(key)


def _apply_template(template: str, tokens: dict[str, str]) -> str:
    rendered = template
    for key, value in tokens.items():
        rendered = rendered.replace("{" + key + "}", value)
    return rendered


def build_theme_stylesheet(effective: EffectiveTheme) -> str:
    """Return application QSS for the effective light or dark theme."""
    colors = load_theme_colors(effective)
    tokens = {
        **colors,
        "secondary_selectors": ",\n".join(_SECONDARY_BUTTONS),
        "tab_selectors": _tab_selectors(),
        "tab_selectors_hover": _tab_selectors(pseudo="hover"),
        "tab_selectors_checked": _tab_selectors(pseudo="checked"),
        "disabled_button_bg": _color(
            colors,
            "button.secondaryBackground",
            fallback=_color(colors, "widget.border"),
        ),
        "tab_hover_bg": _color(
            colors,
            "tab.hoverBackground",
            fallback=_color(colors, "tab.activeBackground"),
        ),
    }
    template = _APP_QSS.read_text(encoding="utf-8")
    return _apply_template(template, tokens)


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
