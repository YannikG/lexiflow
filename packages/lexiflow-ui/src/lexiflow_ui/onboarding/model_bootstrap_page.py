"""Onboarding page that downloads required model artifacts.

Retained for phase 14 re-download UI; v1 onboarding skips this page entirely.
"""

from __future__ import annotations

from lexiflow_core.llm.llama_server import native_llm_operational
from lexiflow_core.models.download import (
    ModelAccessError,
    ModelPinError,
    NetworkError,
)
from lexiflow_core.models.model_hints import (
    artifact_hub_page_url,
    native_llm_hub_page_url,
)
from lexiflow_core.models.requirements import EMBEDDING_MINILM_ID, required_artifact_ids
from lexiflow_core.models.store import ModelStore, ModelStoreError
from PySide6.QtCore import QThread, Slot
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWizardPage,
)
from shiboken6 import isValid

from lexiflow_ui.onboarding.bootstrap_worker import ModelBootstrapWorker
from lexiflow_ui.onboarding.hf_browser import open_url


class ModelBootstrapPage(QWizardPage):
    def __init__(
        self,
        *,
        model_store: ModelStore,
        parent: QWizardPage | None = None,
    ) -> None:
        super().__init__(parent)
        self.setTitle("Download models")
        self.setSubTitle(
            "LexiFlow downloads pinned models on first use. "
            "An internet connection is required."
        )
        self._model_store = model_store
        self._bootstrap_complete = False
        self._thread: QThread | None = None
        self._worker: ModelBootstrapWorker | None = None

        self._status = QLabel("Preparing download…", self)
        self._status.setObjectName("bootstrap_status")
        self._status.setWordWrap(True)
        self._error = QLabel(self)
        self._error.setObjectName("bootstrap_error")
        self._error.setWordWrap(True)
        self._error.hide()
        self._progress = QProgressBar(self)
        self._progress.setObjectName("bootstrap_progress")
        self._progress.setRange(0, 100)
        self._console = QPlainTextEdit(self)
        self._console.setObjectName("bootstrap_console")
        self._console.setReadOnly(True)
        self._console.setMaximumHeight(120)
        self._console.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        console_font = QFont("Menlo")
        if not console_font.exactMatch():
            console_font = QFont("Courier New")
        console_font.setStyleHint(QFont.StyleHint.Monospace)
        self._console.setFont(console_font)
        self._console.hide()
        self._open_gemma = QPushButton("Open model on Hugging Face", self)
        self._open_gemma.setObjectName("bootstrap_open_gemma_button")
        self._open_gemma.hide()
        self._open_gemma.clicked.connect(self._on_open_gemma_hub)
        self._retry = QPushButton("Retry download", self)
        self._retry.setObjectName("bootstrap_retry_button")
        self._retry.hide()
        self._retry.clicked.connect(self._on_retry)
        self._redownload = QPushButton("Re-download models", self)
        self._redownload.setObjectName("bootstrap_redownload_button")
        self._redownload.hide()
        self._redownload.clicked.connect(self._on_redownload)
        self._action_row = QHBoxLayout()
        self._action_row.setSpacing(8)
        self._action_row.addWidget(self._open_gemma)
        self._action_row.addWidget(self._retry)
        self._action_row.addWidget(self._redownload)
        self._action_row.addStretch()

        layout = QVBoxLayout(self)
        layout.addWidget(self._status)
        layout.addWidget(self._progress)
        layout.addWidget(self._console)
        layout.addWidget(self._error)
        layout.addLayout(self._action_row)
        layout.addStretch()

    @property
    def model_store(self) -> ModelStore:
        return self._model_store

    def set_model_store(self, store: ModelStore) -> None:
        """Replace the store used for bootstrap (tests and retry flows)."""
        self._stop_worker()
        self._model_store = store

    @property
    def bootstrap_complete(self) -> bool:
        return self._bootstrap_complete

    def bootstrap_error_text(self) -> str:
        return self._error.text()

    def is_bootstrap_error_visible(self) -> bool:
        return self._error.isVisible()

    def retry_button(self) -> QPushButton:
        return self._retry

    def open_gemma_button(self) -> QPushButton:
        return self._open_gemma

    def redownload_button(self) -> QPushButton:
        return self._redownload

    def initializePage(self) -> None:  # noqa: N802
        self._show_preparing_ui()
        app = QApplication.instance()
        if app is not None:
            app.processEvents()
        self._begin_bootstrap()

    def cleanupPage(self) -> None:  # noqa: N802
        self._stop_worker()

    def _on_retry(self) -> None:
        self._hide_access_actions()
        self._show_preparing_ui()
        self._begin_bootstrap()

    def _on_redownload(self) -> None:
        answer = QMessageBox.question(
            self,
            "Re-download models?",
            "This deletes cached models and downloads them again. "
            "Large models may take a long time.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        self._hide_access_actions()
        self._show_preparing_ui()
        self._begin_bootstrap(force_redownload=True)

    def _on_open_gemma_hub(self) -> None:
        open_url(native_llm_hub_page_url())

    def _hide_access_actions(self) -> None:
        self._error.hide()
        self._open_gemma.hide()
        self._retry.hide()
        self._redownload.hide()

    def _show_preparing_ui(self) -> None:
        self._bootstrap_complete = False
        self._hide_access_actions()
        self._status.setText("Preparing download…")
        self._progress.setRange(0, 0)
        self._progress.setValue(0)
        self._console.clear()
        self._console.hide()
        self.completeChanged.emit()

    def _begin_bootstrap(self, *, force_redownload: bool = False) -> None:
        from lexiflow_ui.onboarding.wizard import OnboardingWizard

        wizard = self.wizard()
        if not isinstance(wizard, OnboardingWizard):
            return

        wizard.settings = wizard.llm_page.apply_to_settings(wizard.settings)
        self._model_store.set_huggingface_token(wizard.settings.huggingface_token)
        if wizard.llm_page.skips_bootstrap_page():
            self._bootstrap_complete = True
            self._progress.setRange(0, 100)
            self._progress.setValue(100)
            self._status.setText("All required models are ready.")
            self._redownload.show()
            self.completeChanged.emit()
            return

        artifact_ids = tuple(required_artifact_ids(wizard.settings))
        all_installed = all(
            self._model_store.is_installed(artifact_id) for artifact_id in artifact_ids
        )
        if all_installed and not force_redownload:
            self._try_complete_embedded_bootstrap(wizard)
            return

        self._status.setText("Downloading required models…")
        self._progress.setRange(0, 0)
        self._console.clear()
        self._console.show()
        self.completeChanged.emit()

        self._stop_worker()
        self._thread = QThread()
        self._worker = ModelBootstrapWorker(
            self._model_store,
            artifact_ids,
            force_redownload=force_redownload,
        )
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.progress_changed.connect(self._on_progress_changed)
        self._worker.log_line_changed.connect(self._on_log_line_changed)
        self._worker.succeeded.connect(self._on_bootstrap_succeeded)
        self._worker.failed.connect(self._on_bootstrap_failed)
        self._worker.succeeded.connect(self._thread.quit)
        self._worker.failed.connect(self._thread.quit)
        self._thread.finished.connect(self._clear_worker_refs)
        self._thread.start()

    @Slot(int, str)
    def _on_progress_changed(self, percent: int, message: str) -> None:
        if self._progress.maximum() == 0:
            self._progress.setRange(0, 100)
        self._progress.setValue(percent)
        self._status.setText(message)

    @Slot(str)
    def _on_log_line_changed(self, line: str) -> None:
        line = line.replace("\r", "").strip()
        if not line:
            return
        if not self._console.isVisible():
            self._console.show()
        text = self._console.toPlainText()
        lines = text.split("\n") if text else []
        live_prefixes = ("Downloading", "Fetching")
        if lines and any(line.startswith(prefix) for prefix in live_prefixes):
            if any(lines[-1].startswith(prefix) for prefix in live_prefixes):
                lines[-1] = line
            else:
                lines.append(line)
        else:
            lines.append(line)
        self._console.setPlainText("\n".join(lines[-50:]))
        scrollbar = self._console.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    @Slot()
    def _on_bootstrap_succeeded(self) -> None:
        from lexiflow_ui.onboarding.wizard import OnboardingWizard

        wizard = self.wizard()
        if not isinstance(wizard, OnboardingWizard):
            return
        self._try_complete_embedded_bootstrap(wizard)

    def _mark_bootstrap_complete(self) -> None:
        self._bootstrap_complete = True
        self._progress.setRange(0, 100)
        self._progress.setValue(100)
        self._status.setText("All required models are ready.")
        self._error.hide()
        self._console.hide()
        self._redownload.show()
        self.completeChanged.emit()

    def _try_complete_embedded_bootstrap(self, wizard: object) -> None:
        from lexiflow_ui.onboarding.wizard import OnboardingWizard

        if not isinstance(wizard, OnboardingWizard):
            return
        if wizard.settings.ollama_url:
            self._mark_bootstrap_complete()
            return
        ready, message = native_llm_operational(wizard.settings)
        if ready:
            self._mark_bootstrap_complete()
            return
        self._bootstrap_complete = False
        self._progress.setRange(0, 100)
        self._progress.setValue(0)
        self._status.setText("llama-server is not ready.")
        self._error.setText(
            message or "Install llama-server from llama.cpp before continuing."
        )
        self._error.show()
        self._retry.show()
        self.completeChanged.emit()

    @Slot(object)
    def _on_bootstrap_failed(self, exc: object) -> None:
        self._bootstrap_complete = False
        self._progress.setRange(0, 100)
        self._progress.setValue(0)
        self._status.setText("Model download failed.")

        if isinstance(exc, ModelPinError):
            self._error.setText(
                "Model manifest pin is invalid. Update LexiFlow or report a bug."
            )
        elif isinstance(exc, ModelAccessError):
            embedding_url = artifact_hub_page_url(EMBEDDING_MINILM_ID)
            self._error.setText(
                "Model download requires Hugging Face access.\n"
                f"Check the model page: {embedding_url}\n"
                "Add a token if needed, then retry."
            )
            self._open_gemma.show()
            self._retry.show()
        elif isinstance(exc, NetworkError):
            self._error.setText(
                "Download failed. Check your network connection and try again."
            )
            self._retry.show()
        elif isinstance(exc, ModelStoreError):
            self._error.setText(str(exc))
            self._retry.show()
        else:
            self._error.setText("Model download failed.")
            self._retry.show()

        self._error.show()
        self.completeChanged.emit()

    @Slot()
    def _clear_worker_refs(self) -> None:
        self._thread = None
        self._worker = None

    def _stop_worker(self) -> None:
        thread = self._thread
        worker = self._worker
        if thread is not None and isValid(thread) and thread.isRunning():
            thread.requestInterruption()
            thread.quit()
            if not thread.wait(5000):
                self._thread = thread
                self._worker = worker
                return
        self._thread = None
        self._worker = None

    def validatePage(self) -> bool:  # noqa: N802
        return self._bootstrap_complete

    def isComplete(self) -> bool:  # noqa: N802
        return self._bootstrap_complete
