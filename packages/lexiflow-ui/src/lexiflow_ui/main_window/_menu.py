"""Menu bar construction for the application shell."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtGui import QAction, QKeySequence

if TYPE_CHECKING:
    from lexiflow_ui.main_window.window import MainWindow


class MainWindowMenuMixin:
    """Builds the main window menu bar and global shortcuts."""

    def _build_menu_bar(self: MainWindow) -> None:
        texts_menu = self.menuBar().addMenu("&Texts")
        self._add_text_menu_action = QAction("Add text…", self)
        self._add_text_menu_action.setShortcut(QKeySequence.StandardKey.New)
        self._add_text_menu_action.triggered.connect(self._open_add_text_dialog)
        texts_menu.addAction(self._add_text_menu_action)

        library_menu = self.menuBar().addMenu("&Library")
        self._switch_language_action = QAction("Switch language…", self)
        self._switch_language_action.triggered.connect(
            self._open_switch_language_dialog
        )
        library_menu.addAction(self._switch_language_action)
        library_menu.addSeparator()
        self._trash_action = QAction("Trash…", self)
        self._trash_action.triggered.connect(self._open_trash_dialog)
        library_menu.addAction(self._trash_action)

        settings_menu = self.menuBar().addMenu("&Settings")
        self._settings_action = QAction("Settings…", self)
        self._settings_action.triggered.connect(self._open_settings_dialog)
        settings_menu.addAction(self._settings_action)
        self._about_action = QAction("About LexiFlow…", self)
        self._about_action.triggered.connect(self._open_about_dialog)
        settings_menu.addAction(self._about_action)

        options_menu = self.menuBar().addMenu("&Options")
        self._export_library_action = QAction("Export library…", self)
        self._export_library_action.triggered.connect(self._export_library_backup)
        options_menu.addAction(self._export_library_action)
        self._restore_library_action = QAction("Restore library to new folder…", self)
        self._restore_library_action.triggered.connect(self._restore_library_backup)
        options_menu.addAction(self._restore_library_action)
        self._replace_library_action = QAction("Replace current library…", self)
        self._replace_library_action.triggered.connect(self._replace_current_library)
        options_menu.addAction(self._replace_library_action)
        options_menu.addSeparator()
        self._rebuild_index_action = QAction("Rebuild library index", self)
        self._rebuild_index_action.triggered.connect(self._rebuild_library_index)
        options_menu.addAction(self._rebuild_index_action)
        options_menu.addSeparator()
        self._export_vocabulary_action = QAction("Export vocabulary…", self)
        options_menu.addAction(self._export_vocabulary_action)
        self._import_vocabulary_action = QAction("Import vocabulary…", self)
        options_menu.addAction(self._import_vocabulary_action)
        options_menu.addSeparator()
        self._remove_language_action = QAction("Delete language…", self)
        self._remove_language_action.triggered.connect(self._remove_target_language)
        options_menu.addAction(self._remove_language_action)

        self._search_action = QAction("Search library", self)
        self._search_action.setShortcut(QKeySequence.StandardKey.Find)
        self._search_action.triggered.connect(self._focus_library_search)
        self.addAction(self._search_action)
