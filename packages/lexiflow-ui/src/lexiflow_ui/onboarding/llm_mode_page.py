"""Wizard page: choose the LLM provider."""

from __future__ import annotations

from enum import Enum

from PySide6.QtWidgets import QRadioButton, QVBoxLayout, QWizardPage


class LlmMode(Enum):
    NATIVE = "native"
    OLLAMA = "ollama"


class LlmModePage(QWizardPage):
    """Radio choice only; configuration is on the following wizard page."""

    PAGE_ID = 2
    CONFIG_PAGE_ID = 3

    def __init__(self, parent: QWizardPage | None = None) -> None:
        super().__init__(parent)
        self.setTitle("LLM setup")
        self.setSubTitle(
            "LexiFlow uses a built-in llama-server by default. "
            "Advanced users can point at an external Ollama server instead."
        )

        self._native = QRadioButton("Built-in LLM (llama-server)", self)
        self._native.setObjectName("native_llm_radio")
        self._ollama = QRadioButton("Ollama (advanced)", self)
        self._ollama.setObjectName("ollama_radio")
        self._native.setChecked(True)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.addWidget(self._native)
        layout.addWidget(self._ollama)
        layout.addStretch()

    def selected_mode(self) -> LlmMode:
        if self._ollama.isChecked():
            return LlmMode.OLLAMA
        return LlmMode.NATIVE

    def select_native(self) -> None:
        self._native.setChecked(True)

    def select_embedded(self) -> None:
        self.select_native()

    def select_ollama(self) -> None:
        self._ollama.setChecked(True)

    def uses_ollama(self) -> bool:
        return self.selected_mode() == LlmMode.OLLAMA

    def uses_native(self) -> bool:
        return self.selected_mode() == LlmMode.NATIVE

    def skips_bootstrap_page(self) -> bool:
        return True

    def nextId(self) -> int:  # noqa: N802
        return self.CONFIG_PAGE_ID

    def validatePage(self) -> bool:  # noqa: N802
        return True
