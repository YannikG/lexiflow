"""Global settings editor."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace
from pathlib import Path

from lexiflow_core.app_reset import reset_local_app
from lexiflow_core.config.settings import Settings, Theme
from lexiflow_core.config.settings_store import SettingsStore
from lexiflow_core.languages.set_native import SetNativeLanguageError
from lexiflow_core.llm.llama_server import pinned_llama_hf_model
from lexiflow_core.models.model_hints import artifact_display_name
from lexiflow_core.models.requirements import NATIVE_LLM_ID
from lexiflow_core.models.store import ModelStore, UpdateAvailable
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from lexiflow_ui.app_relaunch import prompt_restart_lexiflow, relaunch_application
from lexiflow_ui.background_task import run_with_progress_dialog
from lexiflow_ui.dialogs.native_language_dialog import (
    NativeLanguageDialog,
    language_display_name,
)
from lexiflow_ui.llama_server_supervisor import model_requires_hf_token
from lexiflow_ui.onboarding.hf_browser import open_url
from lexiflow_ui.onboarding.llm_config_page import DEFAULT_OLLAMA_URL, HF_TOKEN_URL
from lexiflow_ui.onboarding.llm_mode_page import LlmMode
from lexiflow_ui.onboarding.ollama_probe import OllamaProbe, PlatformOllamaProbe
from lexiflow_ui.shutdown_flow import confirm_application_quit
from lexiflow_ui.theme import apply_app_theme
from lexiflow_ui.worker_supervisor import WorkerSupervisor

_MASKED_TOKEN = "••••••••••••"


def open_settings_dialog(
    parent: QWidget,
    *,
    app: object,
    settings: Settings,
    settings_store: SettingsStore,
    data_root: Path,
    model_store: ModelStore | None = None,
    worker_supervisor: WorkerSupervisor | None = None,
    llama_supervisor: object | None = None,
    on_saved: Callable[[Settings], None],
) -> None:
    dialog = SettingsDialog(
        app=app,
        settings=settings,
        settings_store=settings_store,
        data_root=data_root,
        model_store=model_store,
        worker_supervisor=worker_supervisor,
        llama_supervisor=llama_supervisor,
        parent=parent,
    )
    dialog.setWindowModality(Qt.WindowModality.ApplicationModal)
    dialog.raise_()
    dialog.activateWindow()
    accepted = dialog.exec() == int(QDialog.DialogCode.Accepted)
    if accepted and dialog.saved_settings is not None:
        on_saved(dialog.saved_settings)


class SettingsDialog(QDialog):
    def __init__(
        self,
        *,
        app: object,
        settings: Settings,
        settings_store: SettingsStore,
        data_root: Path,
        model_store: ModelStore | None = None,
        worker_supervisor: WorkerSupervisor | None = None,
        llama_supervisor: object | None = None,
        ollama_probe: OllamaProbe | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("settings_dialog")
        self.setWindowTitle("Settings")
        self.resize(680, 640)
        self._app = app
        self._settings_store = settings_store
        self._data_root = data_root
        self._model_store = model_store
        self._worker_supervisor = worker_supervisor
        self._llama_supervisor = llama_supervisor
        self._probe = (
            ollama_probe if ollama_probe is not None else PlatformOllamaProbe()
        )
        self._initial_settings = settings
        self._pending_native_language = settings.native_language
        self._stored_hf_token = settings.huggingface_token
        self.saved_settings: Settings | None = None

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        body = QWidget(scroll)
        scroll.setWidget(body)
        layout = QVBoxLayout(self)
        layout.addWidget(scroll)
        content = QVBoxLayout(body)

        content.addWidget(self._section_label("General"))
        general = QFormLayout()
        self._theme = QComboBox(body)
        self._theme.setObjectName("settings_theme_combo")
        for value in ("system", "light", "dark"):
            self._theme.addItem(value.capitalize(), value)
        index = self._theme.findData(settings.theme)
        if index >= 0:
            self._theme.setCurrentIndex(index)
        general.addRow("Theme", self._theme)
        content.addLayout(general)

        content.addWidget(self._section_label("Appearance"))
        appearance = QFormLayout()
        self._font_size = QSpinBox(body)
        self._font_size.setObjectName("settings_font_size")
        self._font_size.setRange(8, 32)
        self._font_size.setValue(settings.reader_font_size)
        appearance.addRow("Reader font size", self._font_size)
        content.addLayout(appearance)

        content.addWidget(self._section_label("Languages"))
        languages = QFormLayout()
        self._native_language_label = QLabel(
            language_display_name(settings.native_language),
            body,
        )
        self._native_language_label.setObjectName("settings_native_language_label")
        change_native = QPushButton("Change…", body)
        change_native.setObjectName("settings_change_native_language")
        change_native.clicked.connect(self._change_native_language)
        native_row = QHBoxLayout()
        native_row.addWidget(self._native_language_label, stretch=1)
        native_row.addWidget(change_native)
        languages.addRow("Native language", native_row)
        content.addLayout(languages)

        content.addWidget(self._section_label("LLM provider"))
        llm_layout = QVBoxLayout()
        self._native_llm = QRadioButton("Built-in LLM (llama-server)", body)
        self._native_llm.setObjectName("settings_native_llm_radio")
        self._ollama = QRadioButton("Ollama (advanced)", body)
        self._ollama.setObjectName("settings_ollama_radio")
        if settings.ollama_url:
            self._ollama.setChecked(True)
        else:
            self._native_llm.setChecked(True)
        self._native_llm.toggled.connect(self._sync_llm_fields)
        llm_layout.addWidget(self._native_llm)
        llm_layout.addWidget(self._ollama)
        ollama_row = QHBoxLayout()
        self._ollama_url = QLineEdit(body)
        self._ollama_url.setObjectName("settings_ollama_url")
        self._ollama_url.setText(settings.ollama_url or DEFAULT_OLLAMA_URL)
        self._test_ollama = QPushButton("Test connection", body)
        self._test_ollama.setObjectName("settings_test_ollama")
        self._test_ollama.clicked.connect(self._test_ollama_connection)
        ollama_row.addWidget(self._ollama_url, stretch=1)
        ollama_row.addWidget(self._test_ollama)
        llm_layout.addLayout(ollama_row)
        self._ollama_status = QLabel(body)
        self._ollama_status.setObjectName("settings_ollama_status")
        self._ollama_status.setWordWrap(True)
        llm_layout.addWidget(self._ollama_status)
        content.addLayout(llm_layout)
        self._sync_llm_fields()

        content.addWidget(self._section_label("Hugging Face token"))
        token_layout = QFormLayout()
        self._hf_token = QLineEdit(body)
        self._hf_token.setObjectName("settings_hf_token")
        self._hf_token.setEchoMode(QLineEdit.EchoMode.Password)
        if settings.huggingface_token:
            self._hf_token.setText(_MASKED_TOKEN)
        token_link = QPushButton("Open Hugging Face token settings", body)
        token_link.setObjectName("settings_hf_token_link")
        token_link.clicked.connect(lambda: open_url(HF_TOKEN_URL))
        token_layout.addRow("Token", self._hf_token)
        token_layout.addRow("", token_link)
        content.addLayout(token_layout)

        if model_store is not None:
            content.addWidget(self._section_label("Models"))
            models_layout = QVBoxLayout()
            self._updates_label = QLabel(body)
            self._updates_label.setObjectName("settings_model_updates_label")
            self._updates_label.setWordWrap(True)
            self._download_updates_button = QPushButton("Download updates", body)
            self._download_updates_button.setObjectName("settings_download_updates")
            self._download_updates_button.clicked.connect(self._download_model_updates)
            check_row = QHBoxLayout()
            check_updates = QPushButton("Check for updates", body)
            check_updates.setObjectName("settings_check_updates")
            check_updates.clicked.connect(
                lambda _checked=False: self._check_model_updates(user_initiated=True)
            )
            check_row.addWidget(self._updates_label, stretch=1)
            check_row.addWidget(check_updates)
            models_layout.addLayout(check_row)
            models_layout.addWidget(self._download_updates_button)
            redownload_label = QLabel("Re-download pinned models:", body)
            redownload_label.setObjectName("settings_redownload_label")
            models_layout.addWidget(redownload_label)
            redownload_row = QHBoxLayout()
            for artifact_id in model_store.pinned_artifact_ids():
                button = QPushButton(
                    f"Re-download {artifact_display_name(artifact_id)}…",
                    body,
                )
                button.setObjectName(f"settings_redownload_{artifact_id}")
                button.clicked.connect(
                    lambda _checked=False, aid=artifact_id: self._reinstall_models(
                        [aid]
                    )
                )
                redownload_row.addWidget(button)
            redownload_all = QPushButton("Re-download all…", body)
            redownload_all.setObjectName("settings_redownload_all")
            redownload_all.clicked.connect(
                lambda _checked=False: self._reinstall_models(
                    list(model_store.pinned_artifact_ids())
                )
            )
            redownload_row.addWidget(redownload_all)
            models_layout.addLayout(redownload_row)
            content.addLayout(models_layout)
            self._pending_updates: list[UpdateAvailable] = []
            QTimer.singleShot(
                0,
                lambda: self._check_model_updates(user_initiated=False),
            )

        content.addWidget(self._section_label("Danger zone"))
        reset_button = QPushButton("Reset app…", body)
        reset_button.setObjectName("settings_reset_button")
        reset_button.clicked.connect(self._reset_app)
        content.addWidget(reset_button)
        content.addStretch()

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel,
            parent=self,
        )
        save_button = buttons.button(QDialogButtonBox.StandardButton.Save)
        if save_button is not None:
            save_button.setDefault(True)
            save_button.setAutoDefault(True)
        cancel_button = buttons.button(QDialogButtonBox.StandardButton.Cancel)
        if cancel_button is not None:
            cancel_button.setObjectName("settings_cancel_button")
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    @staticmethod
    def _section_label(text: str) -> QLabel:
        label = QLabel(text)
        font = label.font()
        font.setBold(True)
        label.setFont(font)
        return label

    def _selected_llm_mode(self) -> LlmMode:
        if self._ollama.isChecked():
            return LlmMode.OLLAMA
        return LlmMode.NATIVE

    def _sync_llm_fields(self) -> None:
        use_ollama = self._selected_llm_mode() == LlmMode.OLLAMA
        self._ollama_url.setEnabled(use_ollama)
        self._test_ollama.setEnabled(use_ollama)
        if not use_ollama:
            self._ollama_status.clear()

    def _change_native_language(self) -> None:
        dialog = NativeLanguageDialog(
            current_iso=self._pending_native_language,
            parent=self,
        )
        if dialog.exec() != int(QDialog.DialogCode.Accepted):
            return
        iso = dialog.selected_iso()
        if iso is None:
            return
        if (
            self._initial_settings.active_target_language is not None
            and iso == self._initial_settings.active_target_language
        ):
            QMessageBox.warning(
                self,
                "Native language",
                "Native language must differ from the active target language.",
            )
            return
        self._pending_native_language = iso
        self._native_language_label.setText(language_display_name(iso))

    def _test_ollama_connection(self) -> None:
        url = self._ollama_url.text().strip() or DEFAULT_OLLAMA_URL
        if self._probe.is_available(url):
            self._ollama_status.setText("Ollama is reachable.")
        else:
            self._ollama_status.setText(
                "Could not reach Ollama at that URL. Check that Ollama is running."
            )

    def _model_updates_summary(self, updates: list[UpdateAvailable]) -> str:
        if updates:
            lines = ", ".join(item.artifact_id for item in updates)
            return f"Updates available: {lines}"
        return "All installed models match the current pins."

    def _refresh_updates_label(self, updates: list[UpdateAvailable]) -> None:
        if not hasattr(self, "_updates_label"):
            return
        self._pending_updates = list(updates)
        if not updates:
            self._updates_label.setText("Model pins: up to date.")
            self._download_updates_button.setEnabled(False)
            return
        self._updates_label.setText(self._model_updates_summary(updates))
        self._download_updates_button.setEnabled(True)

    def _check_model_updates(self, *, user_initiated: bool = False) -> None:
        if self._model_store is None:
            return
        updates = self._model_store.check_for_updates()
        self._refresh_updates_label(updates)
        if user_initiated:
            QMessageBox.information(
                self,
                "Model updates",
                self._model_updates_summary(updates),
            )

    def _resolved_hf_token(self) -> str | None:
        raw = self._hf_token.text().strip()
        if not raw:
            return None
        if raw == _MASKED_TOKEN and self._stored_hf_token:
            return self._stored_hf_token
        return raw

    def _artifact_download_requires_token(self, artifact_ids: list[str]) -> bool:
        if NATIVE_LLM_ID not in artifact_ids:
            return False
        try:
            return model_requires_hf_token(pinned_llama_hf_model())
        except RuntimeError:
            return True

    def _download_requires_token(self) -> bool:
        if not self._pending_updates:
            return False
        return self._artifact_download_requires_token(
            [item.artifact_id for item in self._pending_updates]
        )

    def _download_artifacts(
        self,
        artifact_ids: list[str],
        *,
        success_title: str,
        success_message: str,
    ) -> None:
        if self._model_store is None or not artifact_ids:
            return
        token = self._resolved_hf_token()
        if self._artifact_download_requires_token(artifact_ids) and not token:
            QMessageBox.warning(
                self,
                "Hugging Face token required",
                "Set a Hugging Face token first to download gated models.",
            )
            return
        self._model_store.set_huggingface_token(token)
        model_store = self._model_store

        def download_work(
            on_progress: Callable[[float], None],
            on_status: Callable[[str], None],
        ) -> None:
            assert model_store is not None
            for artifact_id in artifact_ids:
                label = artifact_display_name(artifact_id)
                header = f"Downloading {label}"

                def on_log_line(
                    line: str,
                    *,
                    status_header: str = header,
                ) -> None:
                    on_status(f"{status_header}\n{line}")

                on_progress(0.0)
                on_status(f"{header}…")
                model_store.reinstall_artifact(
                    artifact_id,
                    on_progress=on_progress,
                    on_log_line=on_log_line,
                )

        ok, error = run_with_progress_dialog(
            self,
            title="Downloading models",
            initial_status="Preparing download…",
            work=download_work,
        )
        if not ok:
            QMessageBox.critical(self, "Download failed", error or "Download failed.")
            return
        self._check_model_updates()
        QMessageBox.information(self, success_title, success_message)

    def _download_model_updates(self) -> None:
        if self._model_store is None or not self._pending_updates:
            return
        self._download_artifacts(
            [item.artifact_id for item in self._pending_updates],
            success_title="Models updated",
            success_message="Model downloads finished.",
        )

    def _reinstall_models(self, artifact_ids: list[str]) -> None:
        if len(artifact_ids) == 1:
            label = artifact_display_name(artifact_ids[0])
            success_message = f"{label} was re-downloaded."
        else:
            success_message = "Pinned models were re-downloaded."
        self._download_artifacts(
            artifact_ids,
            success_title="Models re-downloaded",
            success_message=success_message,
        )

    def _reset_app(self) -> None:
        confirm = QMessageBox.warning(
            self,
            "Reset app",
            "This permanently deletes all texts, vocabulary, and cached models. "
            "Unsaved edits will be lost.\n\nContinue?",
            QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        if confirm != QMessageBox.StandardButton.Ok:
            return
        typed, ok = QInputDialog.getText(self, "Reset app", "Type RESET to confirm:")
        if not ok or typed.strip() != "RESET":
            return
        if self._worker_supervisor is not None:
            from lexiflow_core.jobs.service import JobService

            job_service = JobService(self._data_root)
            if not confirm_application_quit(
                self,
                job_service=job_service,
                worker_supervisor=self._worker_supervisor,
                llama_supervisor=self._llama_supervisor,  # type: ignore[arg-type]
            ):
                return
        try:
            self.saved_settings = reset_local_app(
                data_root=self._data_root,
                settings_store=self._settings_store,
            )
        except Exception as exc:
            QMessageBox.critical(
                self,
                "Reset failed",
                f"Failed to reset application: {exc}",
            )
            return
        relaunch_application()

    def _provider_changed(self, updated: Settings) -> bool:
        before = self._initial_settings.ollama_url
        after = updated.ollama_url
        return (before is None) != (after is None) or (
            before is not None and after is not None and before != after
        )

    def _hf_token_changed(self, updated: Settings) -> bool:
        return updated.huggingface_token != self._initial_settings.huggingface_token

    def _save(self) -> None:
        theme_value = self._theme.currentData()
        theme: Theme = theme_value if isinstance(theme_value, str) else "system"  # type: ignore[assignment]
        if self._selected_llm_mode() == LlmMode.OLLAMA:
            ollama = self._ollama_url.text().strip() or DEFAULT_OLLAMA_URL
        else:
            ollama = None
        token = self._resolved_hf_token()
        updated = replace(
            self._initial_settings,
            theme=theme,
            reader_font_size=self._font_size.value(),
            native_language=self._pending_native_language,
            ollama_url=ollama,
            huggingface_token=token,
        )
        if self._pending_native_language != self._initial_settings.native_language:
            from lexiflow_core.languages.set_native import set_native_language

            try:
                updated = set_native_language(
                    settings_store=self._settings_store,
                    settings=updated,
                    native_language=self._pending_native_language or "",
                )
            except SetNativeLanguageError as exc:
                QMessageBox.warning(self, "Native language", str(exc))
                return
        else:
            self._settings_store.save(updated)

        self.saved_settings = updated
        if self._model_store is not None:
            self._model_store.set_huggingface_token(token)

        if hasattr(self._app, "setStyleSheet"):
            apply_app_theme(self._app, theme=theme)  # type: ignore[arg-type]

        needs_restart = False
        restart_reason = ""
        if self._provider_changed(updated):
            needs_restart = True
            restart_reason = "LLM provider settings changed."
        elif not updated.ollama_url and self._hf_token_changed(updated):
            needs_restart = True
            restart_reason = "Hugging Face token changed for the built-in LLM."

        self.accept()
        if needs_restart and prompt_restart_lexiflow(self, reason=restart_reason):
            relaunch_application()
