"""Navigation mode switching for the application shell."""

from __future__ import annotations

from typing import TYPE_CHECKING

from lexiflow_ui.main_window._types import NavigationMode

if TYPE_CHECKING:
    from lexiflow_ui.main_window.window import MainWindow


class MainWindowNavigationMixin:
    """Switches between Texts, Vocabulary, and Study content areas."""

    def _show_navigation_mode(self: MainWindow, mode: NavigationMode) -> None:
        if mode != "texts" and not self._confirm_leave_editing_surfaces():
            self._navigation_actions["texts"].setChecked(True)
            return
        action = self._navigation_actions[mode]
        action.setChecked(True)
        self._sidebar.setVisible(mode == "texts")
        mode_widget = {
            "texts": self._texts_stack,
            "vocabulary": self._vocabulary,
            "study": self._study,
        }[mode]
        self._content_stack.setCurrentWidget(mode_widget)
        if mode == "vocabulary":
            self._vocabulary.refresh()
        elif mode == "study":
            self._study.refresh()

    def _on_vocabulary_changed(self: MainWindow) -> None:
        self._vocabulary.refresh()
        self._study.refresh()
        self._reader.refresh_word_panel()
