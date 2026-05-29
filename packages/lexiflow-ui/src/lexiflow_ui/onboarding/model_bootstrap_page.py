"""Onboarding page that downloads required model artifacts."""

from __future__ import annotations

from lexiflow_core.models.download import (
    ModelAccessError,
    ModelPinError,
    NetworkError,
)
from lexiflow_core.models.model_hints import gemma_hub_page_url
from lexiflow_core.models.requirements import required_artifact_ids
from lexiflow_core.models.store import ModelStore
from PySide6.QtCore import QThread, Slot
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
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
        self._open_gemma = QPushButton("Open Gemma on Hugging Face", self)
        self._open_gemma.setObjectName("bootstrap_open_gemma_button")
        self._open_gemma.hide()
        self._open_gemma.clicked.connect(self._on_open_gemma_hub)
        self._retry = QPushButton("Retry download", self)
        self._retry.setObjectName("bootstrap_retry_button")
        self._retry.hide()
        self._retry.clicked.connect(self._on_retry)
        self._action_row = QHBoxLayout()
        self._action_row.setSpacing(8)
        self._action_row.addWidget(self._open_gemma)
        self._action_row.addWidget(self._retry)
        self._action_row.addStretch()

        layout = QVBoxLayout(self)
        layout.addWidget(self._status)
        layout.addWidget(self._progress)
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

    def _on_open_gemma_hub(self) -> None:
        open_url(gemma_hub_page_url())

    def _hide_access_actions(self) -> None:
        self._error.hide()
        self._open_gemma.hide()
        self._retry.hide()

    def _show_preparing_ui(self) -> None:
        self._bootstrap_complete = False
        self._hide_access_actions()
        self._status.setText("Preparing download…")
        self._progress.setRange(0, 0)
        self._progress.setValue(0)
        self.completeChanged.emit()

    def _begin_bootstrap(self) -> None:
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
            self.completeChanged.emit()
            return

        artifact_ids = tuple(required_artifact_ids(wizard.settings))
        all_installed = all(
            self._model_store.is_installed(artifact_id) for artifact_id in artifact_ids
        )
        if all_installed:
            self._bootstrap_complete = True
            self._progress.setRange(0, 100)
            self._progress.setValue(100)
            self._status.setText("All required models are ready.")
            self.completeChanged.emit()
            return

        self._status.setText("Downloading required models…")
        self._progress.setRange(0, 0)
        self.completeChanged.emit()

        self._stop_worker()
        self._thread = QThread()
        self._worker = ModelBootstrapWorker(self._model_store, artifact_ids)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.progress_changed.connect(self._on_progress_changed)
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

    @Slot()
    def _on_bootstrap_succeeded(self) -> None:
        self._bootstrap_complete = True
        self._progress.setRange(0, 100)
        self._progress.setValue(100)
        self._status.setText("All required models are ready.")
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
            gemma_url = gemma_hub_page_url()
            self._error.setText(
                "Gemma is a gated model on Hugging Face.\n"
                "1. Log in at huggingface.co with the same account as your token.\n"
                f"2. Open the model page and accept the license: {gemma_url}\n"
                "3. Click Open Gemma on Hugging Face (or use the link above), "
                "then Retry download."
            )
            self._open_gemma.show()
            self._retry.show()
        elif isinstance(exc, NetworkError):
            self._error.setText(
                "Download failed. Check your network connection and try again."
            )
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
        self._thread = None
        self._worker = None
        if thread is not None and isValid(thread) and thread.isRunning():
            thread.quit()
            thread.wait(5000)

    def validatePage(self) -> bool:  # noqa: N802
        return self._bootstrap_complete

    def isComplete(self) -> bool:  # noqa: N802
        return self._bootstrap_complete
