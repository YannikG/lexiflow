"""Build Qt stylesheets from bundled dark/light theme color tokens."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal

EffectiveTheme = Literal["light", "dark"]

_THEMES_DIR = Path(__file__).resolve().parent / "themes"
_TOKEN_FILES: dict[EffectiveTheme, str] = {
    "dark": "dark_theme.json",
    "light": "light_theme.json",
}

TAB_PUSH_BUTTON_IDS = (
    "reader_tab_native",
    "reader_tab_translated",
    "add_text_tab_native",
    "add_text_tab_target",
)

_TAB_SELECTORS = tuple(
    f"QPushButton#{object_name}" for object_name in TAB_PUSH_BUTTON_IDS
) + ('QPushButton[objectName^="reader_tab_simplified_"]',)


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


def build_theme_stylesheet(effective: EffectiveTheme) -> str:
    """Return application QSS for the effective light or dark theme."""
    colors = load_theme_colors(effective)

    def color(key: str, *, fallback: str | None = None) -> str:
        return _color(colors, key, fallback=fallback)

    secondary_buttons = (
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
    secondary_selectors = ",\n".join(secondary_buttons)
    tab_selectors = _tab_selectors()
    tab_selectors_hover = _tab_selectors(pseudo="hover")
    tab_selectors_checked = _tab_selectors(pseudo="checked")

    disabled_button_bg = color(
        "button.secondaryBackground", fallback=color("widget.border")
    )
    tab_hover_bg = color("tab.hoverBackground", fallback=color("tab.activeBackground"))

    return f"""
* {{
  outline: none;
}}

QWidget {{
  background-color: {color("editor.background")};
  color: {color("foreground")};
  selection-background-color: {color("editor.inactiveSelectionBackground")};
  selection-color: {color("editor.foreground")};
}}

QMainWindow {{
  background-color: {color("editor.background")};
}}

QWidget#sidebar {{
  background-color: {color("sideBar.background")};
  color: {color("sideBar.foreground")};
  border-right: 1px solid {color("sideBar.border")};
}}

QListWidget#sidebar_text_list,
QListWidget#catalog_list {{
  background-color: {color("sideBar.background")};
  color: {color("sideBar.foreground")};
  border: none;
  outline: none;
}}

QListWidget#sidebar_text_list::item,
QListWidget#catalog_list::item {{
  padding: 4px 8px;
}}

QListWidget#sidebar_text_list::item {{
  font-size: 14px;
}}

QLabel#reader_library_title {{
  font-size: 17px;
  font-weight: 600;
}}

QLineEdit#reader_title_edit {{
  font-size: 17px;
  font-weight: 600;
}}

QListWidget#sidebar_text_list::item:hover,
QListWidget#catalog_list::item:hover {{
  background-color: {color("list.hoverBackground")};
}}

QListWidget#sidebar_text_list::item:selected,
QListWidget#catalog_list::item:selected {{
  background-color: {color("list.activeSelectionBackground")};
  color: {color("list.activeSelectionForeground")};
}}

QToolBar#main_toolbar {{
  background: {color("titleBar.activeBackground")};
  color: {color("titleBar.activeForeground")};
  border: none;
  border-bottom: 1px solid {color("titleBar.border")};
  spacing: 4px;
  padding: 2px 4px;
}}

QToolBar#main_toolbar QToolButton {{
  background: transparent;
  color: {color("titleBar.activeForeground")};
  border: none;
  outline: none;
  padding: 4px 8px;
}}

QToolBar#main_toolbar QToolButton:hover {{
  background: {color("list.hoverBackground")};
}}

QToolBar#main_toolbar QToolButton:focus {{
  border: none;
  outline: none;
}}

QToolBar#main_toolbar QToolButton:checked {{
  background: {color("list.activeSelectionBackground")};
  color: {color("list.activeSelectionForeground")};
}}

QMenuBar {{
  background-color: {color("titleBar.activeBackground")};
  color: {color("titleBar.activeForeground")};
  border-bottom: 1px solid {color("titleBar.border")};
}}

QMenuBar::item {{
  padding: 4px 8px;
  background: transparent;
}}

QMenuBar::item:selected {{
  background: {color("list.hoverBackground")};
}}

QMenu {{
  background-color: {color("menu.background")};
  color: {color("menu.foreground")};
  border: 1px solid {color("widget.border")};
}}

QMenu::item:selected {{
  background-color: {color("menu.selectionBackground")};
  color: {color("menu.selectionForeground")};
}}

QStatusBar {{
  background-color: {color("statusBar.background")};
  color: {color("statusBar.foreground")};
  border-top: 1px solid {color("statusBar.border")};
}}

QStatusBar QLabel,
QLabel#worker_status_message {{
  color: {color("statusBar.foreground")};
  background: transparent;
  padding: 2px 4px;
}}

QPushButton {{
  background-color: {color("button.background")};
  color: {color("button.foreground")};
  border: none;
  outline: none;
  padding: 4px 14px;
  border-radius: 2px;
  min-height: 22px;
}}

QPushButton:hover {{
  background-color: {color("button.hoverBackground")};
}}

QPushButton:focus {{
  border: none;
  outline: none;
}}

QPushButton:disabled {{
  color: {color("descriptionForeground")};
  background-color: {disabled_button_bg};
  border: none;
}}

{secondary_selectors} {{
  background-color: {color("button.secondaryBackground")};
  color: {color("button.secondaryForeground")};
  border: none;
  outline: none;
}}

{secondary_selectors}:hover {{
  background-color: {color("button.secondaryHoverBackground")};
}}

{tab_selectors} {{
  background-color: {color("tab.inactiveBackground")};
  color: {color("tab.inactiveForeground")};
  border: none;
  border-top: 2px solid transparent;
  border-bottom: 1px solid {color("tab.border")};
  border-radius: 0;
  padding: 6px 12px;
}}

{tab_selectors_hover} {{
  background-color: {tab_hover_bg};
}}

{tab_selectors_checked} {{
  background-color: {color("tab.activeBackground")};
  color: {color("tab.activeForeground")};
  border-top: 2px solid {color("tab.activeBorderTop")};
}}

QWidget#reader_widget {{
  background-color: {color("editor.background")};
  color: {color("foreground")};
}}

QTextBrowser#reader_read_pane,
QTextBrowser#reader_edit_preview_pane {{
  background-color: {color("reader.background")};
  color: {color("editor.foreground")};
  border: 1px solid {color("reader.border")};
  border-radius: 2px;
  selection-background-color: {color("editor.inactiveSelectionBackground")};
  selection-color: {color("editor.foreground")};
}}

QPlainTextEdit#reader_edit_pane {{
  background-color: {color("input.background")};
  color: {color("editor.foreground")};
  border: 1px solid {color("input.border")};
  border-radius: 2px;
  selection-background-color: {color("editor.inactiveSelectionBackground")};
  selection-color: {color("editor.foreground")};
}}

QWidget#word_panel {{
  background-color: {color("reader.panelBackground")};
  border-top: 1px solid {color("reader.border")};
}}

QWidget#vocabulary_study_card_face {{
  background-color: {color("reader.panelBackground")};
  border: 1px solid {color("reader.border")};
  border-radius: 8px;
}}

QWidget#vocabulary_study_card_face QLabel {{
  background: transparent;
}}

QLabel#vocabulary_study_card_text {{
  font-size: 32px;
  font-weight: 500;
  background: transparent;
}}

QLabel#vocabulary_study_explanation {{
  font-size: 15px;
  color: {color("descriptionForeground")};
  padding-top: 12px;
  background: transparent;
}}

QTableWidget#word_panel_new_table,
QTableWidget#word_panel_learned_table,
QTableWidget#jobs_panel_table {{
  background-color: {color("reader.panelBackground")};
  border: none;
  gridline-color: {color("reader.border")};
}}

QTextBrowser#reader_read_pane QScrollBar:vertical,
QTextBrowser#reader_edit_preview_pane QScrollBar:vertical,
QTableWidget#word_panel_new_table QScrollBar:vertical,
QTableWidget#word_panel_learned_table QScrollBar:vertical,
QTableWidget#jobs_panel_table QScrollBar:vertical {{
  background: {color("reader.scrollbarBackground")};
  width: 10px;
  margin: 0;
}}

QTextBrowser#reader_read_pane QScrollBar::handle:vertical,
QTextBrowser#reader_edit_preview_pane QScrollBar::handle:vertical,
QTableWidget#word_panel_new_table QScrollBar::handle:vertical,
QTableWidget#word_panel_learned_table QScrollBar::handle:vertical,
QTableWidget#jobs_panel_table QScrollBar::handle:vertical {{
  background: {color("reader.scrollbarThumb")};
  min-height: 24px;
  border-radius: 4px;
}}

QTextBrowser#reader_read_pane QScrollBar::handle:vertical:hover,
QTextBrowser#reader_edit_preview_pane QScrollBar::handle:vertical:hover,
QTableWidget#word_panel_new_table QScrollBar::handle:vertical:hover,
QTableWidget#word_panel_learned_table QScrollBar::handle:vertical:hover,
QTableWidget#jobs_panel_table QScrollBar::handle:vertical:hover {{
  background: {color("reader.scrollbarThumbHover")};
}}

QTextBrowser#reader_read_pane QScrollBar:horizontal,
QTextBrowser#reader_edit_preview_pane QScrollBar:horizontal,
QTableWidget#word_panel_new_table QScrollBar:horizontal,
QTableWidget#word_panel_learned_table QScrollBar:horizontal,
QTableWidget#jobs_panel_table QScrollBar:horizontal {{
  background: {color("reader.scrollbarBackground")};
  height: 10px;
  margin: 0;
}}

QTextBrowser#reader_read_pane QScrollBar::handle:horizontal,
QTextBrowser#reader_edit_preview_pane QScrollBar::handle:horizontal,
QTableWidget#word_panel_new_table QScrollBar::handle:horizontal,
QTableWidget#word_panel_learned_table QScrollBar::handle:horizontal,
QTableWidget#jobs_panel_table QScrollBar::handle:horizontal {{
  background: {color("reader.scrollbarThumb")};
  min-width: 24px;
  border-radius: 4px;
}}

QTextBrowser#reader_read_pane QScrollBar::handle:horizontal:hover,
QTextBrowser#reader_edit_preview_pane QScrollBar::handle:horizontal:hover,
QTableWidget#word_panel_new_table QScrollBar::handle:horizontal:hover,
QTableWidget#word_panel_learned_table QScrollBar::handle:horizontal:hover,
QTableWidget#jobs_panel_table QScrollBar::handle:horizontal:hover {{
  background: {color("reader.scrollbarThumbHover")};
}}

QTextBrowser#reader_read_pane QScrollBar::add-line,
QTextBrowser#reader_read_pane QScrollBar::sub-line,
QTextBrowser#reader_read_pane QScrollBar::add-page,
QTextBrowser#reader_read_pane QScrollBar::sub-page,
QTextBrowser#reader_edit_preview_pane QScrollBar::add-line,
QTextBrowser#reader_edit_preview_pane QScrollBar::sub-line,
QTextBrowser#reader_edit_preview_pane QScrollBar::add-page,
QTextBrowser#reader_edit_preview_pane QScrollBar::sub-page,
QTableWidget#word_panel_new_table QScrollBar::add-line,
QTableWidget#word_panel_new_table QScrollBar::sub-line,
QTableWidget#word_panel_new_table QScrollBar::add-page,
QTableWidget#word_panel_new_table QScrollBar::sub-page,
QTableWidget#word_panel_learned_table QScrollBar::add-line,
QTableWidget#word_panel_learned_table QScrollBar::sub-line,
QTableWidget#word_panel_learned_table QScrollBar::add-page,
QTableWidget#word_panel_learned_table QScrollBar::sub-page,
QTableWidget#jobs_panel_table QScrollBar::add-line,
QTableWidget#jobs_panel_table QScrollBar::sub-line,
QTableWidget#jobs_panel_table QScrollBar::add-page,
QTableWidget#jobs_panel_table QScrollBar::sub-page {{
  background: none;
  border: none;
}}

QTextBrowser#reader_read_pane a,
QTextBrowser#reader_edit_preview_pane a {{
  color: {color("textLink.foreground")};
}}

QLineEdit,
QPlainTextEdit,
QTextEdit,
QComboBox {{
  background-color: {color("input.background")};
  color: {color("input.foreground")};
  border: 1px solid {color("input.border")};
  border-radius: 2px;
  padding: 4px 6px;
}}

QLineEdit:focus,
QComboBox:focus,
QPlainTextEdit:focus,
QTextEdit:focus {{
  border: 1px solid {color("focusBorder")};
}}

QComboBox QAbstractItemView {{
  background-color: {color("dropdown.background")};
  color: {color("dropdown.foreground")};
  border: 1px solid {color("dropdown.border")};
  selection-background-color: {color("list.activeSelectionBackground")};
  selection-color: {color("list.activeSelectionForeground")};
}}

QDialog,
QWizard {{
  background-color: {color("editorWidget.background")};
  color: {color("foreground")};
}}

QLabel#sidebar_empty_label,
QLabel#empty_state_message,
QLabel#descriptionForeground {{
  color: {color("descriptionForeground")};
}}

QSplitter::handle {{
  background: {color("widget.border")};
}}

QScrollBar:vertical {{
  background: {color("editor.background")};
  width: 10px;
  margin: 0;
}}

QScrollBar::handle:vertical {{
  background: {color("widget.border")};
  min-height: 24px;
  border-radius: 4px;
}}

QScrollBar:horizontal {{
  background: {color("editor.background")};
  height: 10px;
  margin: 0;
}}

QScrollBar::handle:horizontal {{
  background: {color("widget.border")};
  min-width: 24px;
  border-radius: 4px;
}}

QScrollBar::add-line,
QScrollBar::sub-line,
QScrollBar::add-page,
QScrollBar::sub-page {{
  background: none;
  border: none;
}}

QProgressBar {{
  background-color: {color("input.background")};
  border: 1px solid {color("input.border")};
  text-align: center;
  color: {color("foreground")};
}}

QProgressBar::chunk {{
  background-color: {color("button.background")};
}}

QRadioButton,
QCheckBox {{
  color: {color("foreground")};
  spacing: 6px;
}}

QMessageBox {{
  background-color: {color("editorWidget.background")};
}}
"""
