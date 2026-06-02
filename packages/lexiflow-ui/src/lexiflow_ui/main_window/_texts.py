"""Texts sidebar, reader navigation, and library search."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING
from uuid import UUID

from lexiflow_core.jobs.service import JobService
from lexiflow_core.library.reader_tabs import NATIVE_TAB
from lexiflow_core.library.search_models import SearchHit
from PySide6.QtWidgets import QMessageBox, QPushButton

from lexiflow_ui.add_text_flow import submit_add_text
from lexiflow_ui.dialogs.add_text_dialog import open_add_text_dialog
from lexiflow_ui.find_in_texts_flow import find_in_texts
from lexiflow_ui.reader_flow import (
    list_texts_for_sidebar,
    persist_last_viewed_tab,
    resolve_initial_tab,
)
from lexiflow_ui.unsaved_changes import DirtyEditor, confirm_leave_dirty_editors

if TYPE_CHECKING:
    from lexiflow_ui.main_window.window import MainWindow


class MainWindowTextsMixin:
    """Texts mode: sidebar list, reader, add-text flow, and search hits."""

    def _can_add_text(self: MainWindow) -> bool:
        return self._settings.active_target_language is not None

    def _update_add_text_enabled(self: MainWindow) -> None:
        enabled = self._can_add_text()
        self._add_text_menu_action.setEnabled(enabled)
        self._sidebar.add_text_button().setEnabled(enabled)
        action = self._texts_view.action_button()
        if action is not None:
            action.setEnabled(enabled)

    def _refresh_texts_ui(self: MainWindow) -> None:
        titles = list_texts_for_sidebar(
            self._data_root, self._settings.active_target_language
        )
        self._sidebar.set_texts(titles)
        title_ids = {record.id for record in titles}
        if self._open_text_id is not None and self._open_text_id not in title_ids:
            self._close_open_text()
        if titles:
            self._texts_view.set_content(
                title="Texts in your library",
                message="Select a text in the sidebar to open the reader.",
                show_action=False,
            )
            if self._open_text_id is not None:
                self._sidebar.select_text(self._open_text_id)
                self._texts_stack.setCurrentWidget(self._reader)
            else:
                self._show_texts_placeholder()
        else:
            self._texts_view.set_content(
                title="No texts yet",
                message="Add a text to start reading and building vocabulary.",
                show_action=True,
            )
            self._close_open_text()
            self._show_texts_placeholder()
        self._update_add_text_enabled()

    def _close_open_text(self: MainWindow) -> None:
        self._open_text_id = None
        self._reader.close_open_text()

    def _show_texts_placeholder(self: MainWindow) -> None:
        self._texts_stack.setCurrentWidget(self._texts_view)

    def _dirty_editors(self: MainWindow) -> tuple[DirtyEditor, ...]:
        return (self._reader,)

    def _confirm_leave_editing_surfaces(self: MainWindow) -> bool:
        return confirm_leave_dirty_editors(self, self._dirty_editors())

    def _open_reader_for_text(self: MainWindow, text_id: UUID) -> None:
        if (
            self._open_text_id == text_id
            and self._texts_stack.currentWidget() is self._reader
            and self._reader.is_editing()
        ):
            self._sidebar.select_text(text_id)
            return
        record = self._text_repository.get_text(text_id)
        initial_tab = resolve_initial_tab(self._library_index, record)
        opened = self._reader.open_text(
            record=record,
            repo=self._text_repository,
            index=self._library_index,
            settings=self._settings,
            initial_tab=initial_tab,
        )
        if not opened:
            if self._open_text_id is not None:
                self._sidebar.select_text(self._open_text_id)
            return
        self._open_text_id = text_id
        self._texts_stack.setCurrentWidget(self._reader)

    def _open_reader_for_search_hit(
        self: MainWindow,
        hit: SearchHit,
        *,
        query: str,
    ) -> None:
        if not self._confirm_leave_editing_surfaces():
            return
        texts_action = self._navigation_actions.get("texts")
        if texts_action is not None:
            texts_action.setChecked(True)
        self._show_navigation_mode("texts")
        record = self._text_repository.get_text(hit.text_id)
        opened = self._reader.open_text(
            record=record,
            repo=self._text_repository,
            index=self._library_index,
            settings=self._settings,
            initial_tab=hit.variant,
        )
        if not opened:
            return
        self._open_text_id = hit.text_id
        self._sidebar.select_text(hit.text_id)
        self._texts_stack.setCurrentWidget(self._reader)
        self._reader.scroll_to_match(query)

    def _on_library_search_hit(self: MainWindow, hit: SearchHit) -> None:
        self._open_reader_for_search_hit(
            hit,
            query=self._search_query_from_hit(hit),
        )

    def _focus_library_search(self: MainWindow) -> None:
        if self._settings.active_target_language is None:
            QMessageBox.information(
                self,
                "Search",
                "Finish language setup before searching the library.",
            )
            return
        self._toolbar_search.focus_search()

    def _search_query_from_hit(self: MainWindow, hit: SearchHit) -> str:
        match = re.search(r"<mark>(.*?)</mark>", hit.snippet)
        if match is not None:
            return match.group(1)
        return hit.title

    def _find_in_texts_for_lemma(self: MainWindow, lemma: str) -> None:
        language = self._settings.active_target_language
        if language is None:
            return
        find_in_texts(
            self,
            index=self._library_index,
            language_code=language,
            query=lemma,
            on_hit_selected=lambda hit: self._open_reader_for_search_hit(
                hit,
                query=lemma,
            ),
        )

    def _on_reader_tab_changed(self: MainWindow, tab_id: str) -> None:
        if self._open_text_id is None:
            return
        persist_last_viewed_tab(self._library_index, self._open_text_id, tab_id)

    def _on_reader_text_deleted(self: MainWindow) -> None:
        self._close_open_text()
        self._refresh_texts_ui()

    def _open_add_text_dialog(self: MainWindow) -> None:
        if not self._can_add_text():
            QMessageBox.information(
                self,
                "Add text",
                "Finish language setup in onboarding before adding texts.",
            )
            return
        if not self._confirm_leave_editing_surfaces():
            return
        target = self._settings.active_target_language
        assert target is not None
        form = open_add_text_dialog(
            data_root=self._data_root,
            target_language=target,
            parent=self,
        )
        if form is None:
            return
        text_id = submit_add_text(
            data_root=self._data_root,
            settings=self._settings,
            form=form,
            parent=self,
        )
        if text_id is None:
            return
        self._refresh_texts_ui()
        self._open_reader_for_text(text_id)
        self._reader.select_tab(NATIVE_TAB)
        self._ensure_background_workers(JobService(self._data_root))
        self._schedule_reader_refresh()
        self._schedule_library_refresh()

    def _schedule_library_refresh(self: MainWindow) -> None:
        """Re-read the library index while background jobs may update titles."""
        from PySide6.QtCore import QTimer

        for delay_ms in (500, 2000, 5000, 10000, 20000, 40000):
            QTimer.singleShot(delay_ms, lambda: self._refresh_texts_ui())

    def texts_empty_action_button(self: MainWindow) -> QPushButton | None:
        """Add text button in the Texts empty state, when shown."""
        return self._texts_view.action_button()
