"""Toolbar and central layout for the application shell."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QActionGroup
from PySide6.QtWidgets import QHBoxLayout, QStackedWidget, QToolBar, QWidget

from lexiflow_ui.main_window._types import SIDEBAR_WIDTH
from lexiflow_ui.widgets.active_target_language import ActiveTargetLanguageWidget
from lexiflow_ui.widgets.empty_state import EmptyStateWidget
from lexiflow_ui.widgets.library_search_field import LibrarySearchField
from lexiflow_ui.widgets.reader_widget import ReaderWidget
from lexiflow_ui.widgets.sidebar import SidebarWidget
from lexiflow_ui.widgets.study_widget import StudyWidget
from lexiflow_ui.widgets.vocabulary_widget import VocabularyWidget

if TYPE_CHECKING:
    from lexiflow_ui.main_window.window import MainWindow


class MainWindowChromeMixin:
    """Builds toolbar navigation and the sidebar / content stack."""

    def _build_toolbar(self: MainWindow) -> None:
        toolbar = QToolBar("Main", self)
        toolbar.setObjectName("main_toolbar")
        toolbar.setMovable(False)
        toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
        self.addToolBar(toolbar)
        if self._settings.active_target_language is not None:
            self._active_target_language = ActiveTargetLanguageWidget(
                settings=self._settings,
                data_root=self._data_root,
                parent=self,
            )
            toolbar.addWidget(self._active_target_language)
            toolbar.addSeparator()
        group = QActionGroup(self)
        group.setExclusive(True)
        for mode, label in (
            ("texts", "Texts"),
            ("vocabulary", "Vocabulary"),
            ("study", "Study"),
        ):
            action = QAction(label, self)
            action.setCheckable(True)
            action.triggered.connect(
                lambda _checked=False, m=mode: self._show_navigation_mode(m)
            )
            group.addAction(action)
            toolbar.addAction(action)
            self._navigation_actions[mode] = action
        toolbar.addSeparator()
        self._toolbar_search = LibrarySearchField(
            index=self._library_index,
            language_code=lambda: self._settings.active_target_language,
            object_name="toolbar_search",
            parent=toolbar,
        )
        self._toolbar_search.setMinimumWidth(220)
        self._toolbar_search.hit_selected.connect(self._on_library_search_hit)
        toolbar.addWidget(self._toolbar_search)

    def _build_central_layout(self: MainWindow) -> None:
        container = QWidget(self)
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        self._sidebar = SidebarWidget(container)
        self._sidebar.setFixedWidth(SIDEBAR_WIDTH)
        self._sidebar.add_text_button().clicked.connect(self._open_add_text_dialog)
        self._sidebar.text_selected.connect(self._open_reader_for_text)
        self._texts_stack = QStackedWidget(container)
        self._texts_stack.setObjectName("texts_content_stack")
        self._texts_view = EmptyStateWidget(
            title="No texts yet",
            message="Add a text to start reading and building vocabulary.",
            action_text="Add text",
            parent=self._texts_stack,
        )
        texts_action_button = self._texts_view.action_button()
        if texts_action_button is not None:
            texts_action_button.clicked.connect(self._open_add_text_dialog)
        self._reader = ReaderWidget(
            self._texts_stack,
            data_root=self._data_root,
            supervisor=self._supervisor,
            llama_supervisor=self._llama_supervisor,
        )
        self._reader.tab_changed.connect(self._on_reader_tab_changed)
        self._reader.text_saved.connect(self._refresh_texts_ui)
        self._reader.text_deleted.connect(self._on_reader_text_deleted)
        self._reader.simplify_submitted.connect(self._on_simplify_submitted)
        self._supervisor.state_changed.connect(self._on_infrastructure_state_changed)
        self._texts_stack.addWidget(self._texts_view)
        self._texts_stack.addWidget(self._reader)
        self._content_stack = QStackedWidget(container)
        self._vocabulary = VocabularyWidget(
            data_root=self._data_root,
            settings=self._settings,
            supervisor=self._supervisor,
            parent=self._content_stack,
        )
        self._vocabulary.vocabulary_changed.connect(self._on_vocabulary_changed)
        self._vocabulary.find_in_texts_requested.connect(self._find_in_texts_for_lemma)
        self._export_vocabulary_action.triggered.connect(
            self._vocabulary.export_vocabulary
        )
        self._import_vocabulary_action.triggered.connect(
            self._vocabulary.import_vocabulary
        )
        self._study = StudyWidget(
            data_root=self._data_root,
            settings=self._settings,
            parent=self._content_stack,
        )
        self._study.vocabulary_changed.connect(self._on_vocabulary_changed)
        self._reader.vocabulary_changed.connect(self._on_vocabulary_changed)
        self._content_stack.addWidget(self._texts_stack)
        self._content_stack.addWidget(self._vocabulary)
        self._content_stack.addWidget(self._study)
        layout.addWidget(self._sidebar)
        layout.addWidget(self._content_stack, stretch=1)
        self.setCentralWidget(container)
