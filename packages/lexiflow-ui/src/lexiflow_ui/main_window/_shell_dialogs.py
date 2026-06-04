"""Menu-driven dialogs: settings, library data, languages, jobs."""

from __future__ import annotations

from typing import TYPE_CHECKING

import lexiflow_core
from lexiflow_core.config.settings import Settings
from lexiflow_core.models.huggingface_downloader import HuggingFaceModelDownloader
from lexiflow_core.models.store import ModelStore
from PySide6.QtWidgets import QMessageBox

from lexiflow_ui.dialogs.jobs_panel_dialog import open_jobs_panel
from lexiflow_ui.dialogs.trash_dialog import open_trash_dialog
from lexiflow_ui.library_options_flow import (
    export_library_backup,
    rebuild_library_index,
    replace_current_library,
    restore_library_to_new_folder,
)
from lexiflow_ui.onboarding.system_info import SystemInfo
from lexiflow_ui.remove_target_language_flow import offer_remove_target_language
from lexiflow_ui.switch_language_flow import open_switch_language_dialog

if TYPE_CHECKING:
    from lexiflow_ui.main_window.window import MainWindow


class MainWindowShellDialogsMixin:
    """Opens shell dialogs and applies settings / library changes."""

    def _open_settings_dialog(self: MainWindow) -> None:
        if not self._confirm_leave_editing_surfaces():
            return
        from lexiflow_core.config.settings_store import SettingsStore
        from PySide6.QtWidgets import QApplication

        from lexiflow_ui.dialogs.settings_dialog import open_settings_dialog

        app = QApplication.instance()
        model_store = ModelStore(
            self._data_root,
            downloader=HuggingFaceModelDownloader(),
            huggingface_token=self._settings.huggingface_token,
        )
        open_settings_dialog(
            self,
            app=app,
            settings=self._settings,
            settings_store=SettingsStore(),
            data_root=self._data_root,
            model_store=model_store,
            worker_supervisor=self._supervisor,
            llama_supervisor=self._llama_supervisor,
            on_saved=self._on_settings_saved,
        )

    def _apply_settings_to_shell(self: MainWindow, settings: Settings) -> None:
        self._settings = settings
        if self._active_target_language is not None:
            self._active_target_language.refresh(
                settings=settings,
                data_root=self._data_root,
            )
        self._vocabulary.apply_settings(settings)
        self._study.apply_settings(settings)

    def _on_settings_saved(self: MainWindow, settings: Settings) -> None:
        self._apply_settings_to_shell(settings)
        self._reader.reload_font_from_settings(settings)

    def _open_about_dialog(self: MainWindow) -> None:
        info = SystemInfo()
        gib = info.total_ram_bytes() / (1024**3)
        QMessageBox.information(
            self,
            "About LexiFlow",
            f"LexiFlow {lexiflow_core.__version__}\n\n"
            f"Recommended RAM: 8 GiB or more\n"
            f"Detected RAM: {gib:.1f} GiB\n\n"
            "Apache 2.0 — local-first language learning.",
        )

    def _open_switch_language_dialog(self: MainWindow) -> None:
        from lexiflow_core.config.settings_store import SettingsStore

        open_switch_language_dialog(
            self,
            data_root=self._data_root,
            settings=self._settings,
            settings_store=SettingsStore(),
            on_switched=self._on_active_language_changed,
        )

    def _on_active_language_changed(self: MainWindow, settings: Settings) -> None:
        self._apply_settings_to_shell(settings)
        self._seen_completed_job_ids.clear()
        self._seen_failed_job_ids.clear()
        self._close_open_text()
        self._refresh_texts_ui()
        self._show_navigation_mode("texts")

    def _open_trash_dialog(self: MainWindow) -> None:
        open_trash_dialog(
            self,
            data_root=self._data_root,
            language_code=self._settings.active_target_language,
            text_repository=self._text_repository,
            supervisor=self._supervisor,
        )
        self._refresh_texts_ui()
        self._vocabulary.refresh()
        self._on_vocabulary_changed()

    def _export_library_backup(self: MainWindow) -> None:
        export_library_backup(parent=self, data_root=self._data_root)

    def _restore_library_backup(self: MainWindow) -> None:
        restore_library_to_new_folder(parent=self)

    def _replace_current_library(self: MainWindow) -> None:
        if replace_current_library(
            parent=self,
            data_root=self._data_root,
            library_index=self._library_index,
        ):
            self._refresh_texts_ui()
            self._vocabulary.refresh()

    def _rebuild_library_index(self: MainWindow) -> None:
        rebuild_library_index(
            parent=self,
            data_root=self._data_root,
            library_index=self._library_index,
            language_code=self._settings.active_target_language,
        )
        self._refresh_texts_ui()

    def _remove_target_language(self: MainWindow) -> None:
        iso = self._settings.active_target_language
        if iso is None:
            QMessageBox.information(
                self,
                "Delete language",
                "No active target language is configured.",
            )
            return
        from lexiflow_core.config.settings_store import SettingsStore

        updated = offer_remove_target_language(
            self,
            data_root=self._data_root,
            language_code=iso,
            settings=self._settings,
            settings_store=SettingsStore(),
        )
        if updated is None:
            return
        self._apply_settings_to_shell(updated)
        self._refresh_texts_ui()
        self._open_switch_language_dialog()

    def _on_worker_crashed(self: MainWindow, exit_code: int) -> None:
        answer = QMessageBox.question(
            self,
            "Worker stopped",
            f"The background worker exited unexpectedly (code {exit_code}).\n\n"
            "Restart the worker to resume pending jobs?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes,
        )
        if answer == QMessageBox.StandardButton.Yes:
            from lexiflow_ui.ai_worker_startup import ensure_background_workers

            ensure_background_workers(
                self._supervisor,
                llama_supervisor=self._llama_supervisor,
                embed_supervisor=self._embed_supervisor,
            )

    def _open_jobs_panel(self: MainWindow) -> None:
        open_jobs_panel(self, data_root=self._data_root)
