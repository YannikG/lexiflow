"""Wizard page: choose how LexiFlow loads LLM and embedding models."""

from __future__ import annotations

from enum import Enum

from PySide6.QtWidgets import QRadioButton, QVBoxLayout, QWizardPage


class LlmMode(Enum):
    HF_DOWNLOAD = "hf_download"
    OLLAMA = "ollama"
    MANUAL_IMPORT = "manual_import"


class LlmModePage(QWizardPage):
    """Radio choice only; configuration is on the following wizard page."""

    PAGE_ID = 2
    CONFIG_PAGE_ID = 3

    def __init__(self, parent: QWizardPage | None = None) -> None:
        super().__init__(parent)
        self.setTitle("LLM and embedding setup")
        self.setSubTitle(
            "Choose how LexiFlow loads the LLM and the embedding model. "
            "You will configure the option on the next step."
        )

        self._hf_download = QRadioButton("Download models from Hugging Face", self)
        self._hf_download.setObjectName("hf_download_radio")
        self._ollama = QRadioButton("Use Ollama for the LLM", self)
        self._ollama.setObjectName("ollama_radio")
        self._manual = QRadioButton("Import model folders from disk", self)
        self._manual.setObjectName("manual_import_radio")
        self._hf_download.setChecked(True)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.addWidget(self._hf_download)
        layout.addWidget(self._ollama)
        layout.addWidget(self._manual)
        layout.addStretch()

    def selected_mode(self) -> LlmMode:
        if self._manual.isChecked():
            return LlmMode.MANUAL_IMPORT
        if self._ollama.isChecked():
            return LlmMode.OLLAMA
        return LlmMode.HF_DOWNLOAD

    def select_embedded(self) -> None:
        self._hf_download.setChecked(True)

    def select_ollama(self) -> None:
        self._ollama.setChecked(True)

    def select_manual_import(self) -> None:
        self._manual.setChecked(True)

    def uses_ollama(self) -> bool:
        return self.selected_mode() == LlmMode.OLLAMA

    def uses_embedded_hf_download(self) -> bool:
        return self.selected_mode() == LlmMode.HF_DOWNLOAD

    def skips_bootstrap_page(self) -> bool:
        return self.selected_mode() != LlmMode.HF_DOWNLOAD

    def nextId(self) -> int:  # noqa: N802
        return self.CONFIG_PAGE_ID

    def validatePage(self) -> bool:  # noqa: N802
        return True
