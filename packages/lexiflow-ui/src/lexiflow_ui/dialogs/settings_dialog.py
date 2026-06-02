"""Global settings editor."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace
from pathlib import Path

from lexiflow_core.app_reset import reset_local_app
from lexiflow_core.config.settings import Settings, Theme
from lexiflow_core.config.settings_store import SettingsStore
from lexiflow_core.models.store import ModelStore, UpdateAvailable
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from lexiflow_ui.theme import apply_app_theme


def open_settings_dialog(
    parent: QWidget,
    *,
    app: object,
    settings: Settings,
    settings_store: SettingsStore,
    data_root: Path,
    model_store: ModelStore | None = None,
    on_saved: Callable[[Settings], None],
) -> None:
    dialog = SettingsDialog(
        app=app,
        settings=settings,
        settings_store=settings_store,
        data_root=data_root,
        model_store=model_store,
        parent=parent,
    )
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
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("settings_dialog")
        self.setWindowTitle("Settings")
        self._app = app
        self._settings_store = settings_store
        self._data_root = data_root
        self._model_store = model_store
        self._initial_settings = settings
        self.saved_settings: Settings | None = None

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self._theme = QComboBox(self)
        self._theme.setObjectName("settings_theme_combo")
        for value in ("system", "light", "dark"):
            self._theme.addItem(value.capitalize(), value)
        index = self._theme.findData(settings.theme)
        if index >= 0:
            self._theme.setCurrentIndex(index)
        form.addRow("Theme", self._theme)

        self._font_size = QSpinBox(self)
        self._font_size.setObjectName("settings_font_size")
        self._font_size.setRange(8, 32)
        self._font_size.setValue(settings.reader_font_size)
        form.addRow("Reader font size", self._font_size)

        self._ollama_url = QLineEdit(self)
        self._ollama_url.setObjectName("settings_ollama_url")
        self._ollama_url.setText(settings.ollama_url or "")
        form.addRow("Ollama URL", self._ollama_url)

        self._hf_token = QLineEdit(self)
        self._hf_token.setObjectName("settings_hf_token")
        self._hf_token.setEchoMode(QLineEdit.EchoMode.Password)
        self._hf_token.setText(settings.huggingface_token or "")
        form.addRow("Hugging Face token", self._hf_token)

        self._llm_enabled = QCheckBox("LLM enabled", self)
        self._llm_enabled.setObjectName("settings_llm_enabled")
        self._llm_enabled.setChecked(settings.llm_enabled)
        form.addRow(self._llm_enabled)

        layout.addLayout(form)

        if model_store is not None:
            updates_row = QHBoxLayout()
            self._updates_label = QLabel(self)
            self._updates_label.setObjectName("settings_model_updates_label")
            self._check_updates_button = QPushButton("Check model updates", self)
            self._check_updates_button.clicked.connect(self._check_model_updates)
            updates_row.addWidget(self._updates_label, stretch=1)
            updates_row.addWidget(self._check_updates_button)
            layout.addLayout(updates_row)
            self._refresh_updates_label([])

        reset_button = QPushButton("Reset app…", self)
        reset_button.setObjectName("settings_reset_button")
        reset_button.clicked.connect(self._reset_app)
        layout.addWidget(reset_button)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel,
            parent=self,
        )
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _refresh_updates_label(self, updates: list[UpdateAvailable]) -> None:
        if not hasattr(self, "_updates_label"):
            return
        if not updates:
            self._updates_label.setText("Model pins: up to date.")
            return
        lines = ", ".join(item.artifact_id for item in updates)
        self._updates_label.setText(f"Updates available: {lines}")

    def _check_model_updates(self) -> None:
        if self._model_store is None:
            return
        self._refresh_updates_label(self._model_store.check_for_updates())

    def _reset_app(self) -> None:
        confirm = QMessageBox.warning(
            self,
            "Reset app",
            "This permanently deletes all texts, vocabulary, and cached models. "
            "Type RESET to confirm.",
            QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        if confirm != QMessageBox.StandardButton.Ok:
            return
        typed, ok = QInputDialog.getText(self, "Reset app", "Type RESET to confirm:")
        if not ok or typed.strip() != "RESET":
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
        self.accept()

    def _save(self) -> None:
        theme_value = self._theme.currentData()
        theme: Theme = theme_value if isinstance(theme_value, str) else "system"  # type: ignore[assignment]
        ollama = self._ollama_url.text().strip() or None
        token = self._hf_token.text().strip() or None
        updated = replace(
            self._initial_settings,
            theme=theme,
            reader_font_size=self._font_size.value(),
            ollama_url=ollama,
            huggingface_token=token,
            llm_enabled=self._llm_enabled.isChecked(),
        )
        self._settings_store.save(updated)
        self.saved_settings = updated
        if hasattr(self._app, "setStyleSheet"):
            apply_app_theme(self._app, theme=theme)  # type: ignore[arg-type]
        self.accept()
