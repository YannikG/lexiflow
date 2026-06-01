"""Wizard page: configure native llama-server or Ollama."""

from __future__ import annotations

from dataclasses import replace

from lexiflow_core.config.settings import Settings
from lexiflow_core.llm.llama_server import native_llm_operational
from lexiflow_core.models.model_hints import native_llm_hub_page_url
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
    QWizardPage,
)

from lexiflow_ui.onboarding.hf_browser import open_url
from lexiflow_ui.onboarding.llm_mode_page import LlmMode, LlmModePage
from lexiflow_ui.onboarding.ollama_probe import OllamaProbe, PlatformOllamaProbe

DEFAULT_OLLAMA_URL = "http://127.0.0.1:11434"
HF_TOKEN_URL = "https://huggingface.co/settings/tokens"
HF_HOME_URL = "https://huggingface.co"
_LINE_EDIT_MIN_HEIGHT = 32
TARGET_PAGE_ID = 4


def _line_edit(parent: QWidget, *, placeholder: str = "") -> QLineEdit:
    edit = QLineEdit(parent)
    edit.setMinimumHeight(_LINE_EDIT_MIN_HEIGHT)
    edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
    if placeholder:
        edit.setPlaceholderText(placeholder)
    return edit


def _hint_label(parent: QWidget, text: str, *, object_name: str) -> QLabel:
    label = QLabel(text, parent)
    label.setObjectName(object_name)
    label.setWordWrap(True)
    label.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
    return label


class LlmConfigPage(QWizardPage):
    PAGE_ID = 3

    def __init__(
        self,
        *,
        ollama_probe: OllamaProbe | None = None,
        parent: QWizardPage | None = None,
    ) -> None:
        super().__init__(parent)
        self._probe = (
            ollama_probe if ollama_probe is not None else PlatformOllamaProbe()
        )

        self._content = QWidget(self)
        self._content.setSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum
        )
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setContentsMargins(0, 0, 0, 0)
        self._content_layout.setSpacing(8)
        self._content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        native_panel = QWidget(self._content)
        native_layout = QVBoxLayout(native_panel)
        native_layout.setContentsMargins(0, 0, 0, 0)
        native_layout.setSpacing(8)
        native_layout.addWidget(
            _hint_label(
                native_panel,
                "LexiFlow runs a pinned language model with llama-server. "
                "Models load from Hugging Face when needed. "
                "Install llama-server from llama.cpp before continuing.",
                object_name="native_llm_note",
            )
        )
        self._native_license_steps = _hint_label(
            native_panel,
            "",
            object_name="native_license_steps",
        )
        native_layout.addWidget(self._native_license_steps)
        self._open_native_hub = QPushButton("Open model on Hugging Face", native_panel)
        self._open_native_hub.setObjectName("open_native_hub_button")
        self._open_native_hub.clicked.connect(self._on_open_native_hub)
        native_layout.addWidget(self._open_native_hub)
        self._native_panel = native_panel

        ollama_panel = QWidget(self._content)
        ollama_layout = QVBoxLayout(ollama_panel)
        ollama_layout.setContentsMargins(0, 0, 0, 0)
        ollama_layout.setSpacing(8)
        ollama_layout.addWidget(QLabel("Ollama URL", ollama_panel))
        self._url = _line_edit(ollama_panel)
        self._url.setObjectName("ollama_url_field")
        self._url.setText(DEFAULT_OLLAMA_URL)
        ollama_layout.addWidget(self._url)
        detect_btn = QPushButton("Detect Ollama", ollama_panel)
        detect_btn.setObjectName("ollama_detect_button")
        detect_btn.clicked.connect(self._on_detect)
        self._detect_status = _hint_label(
            ollama_panel, "", object_name="ollama_detect_status"
        )
        detect_row = QHBoxLayout()
        detect_row.addWidget(detect_btn)
        detect_row.addWidget(self._detect_status, stretch=1)
        ollama_layout.addLayout(detect_row)
        ollama_layout.addWidget(
            _hint_label(
                ollama_panel,
                "Ollama runs translate, simplify, and cleanup. "
                "Embeddings also load from Hugging Face when needed.",
                object_name="ollama_embedding_note",
            )
        )
        self._ollama_panel = ollama_panel

        self._hf_token_section = QWidget(self._content)
        token_layout = QVBoxLayout(self._hf_token_section)
        token_layout.setContentsMargins(0, 0, 0, 0)
        token_layout.setSpacing(8)
        token_layout.addWidget(QLabel("Hugging Face token", self._hf_token_section))
        self._hf_token = _line_edit(
            self._hf_token_section, placeholder="Optional Hugging Face token (hf_…)"
        )
        self._hf_token.setObjectName("hf_token_field")
        self._hf_token.setEchoMode(QLineEdit.EchoMode.Password)
        token_layout.addWidget(self._hf_token)
        token_link = QLabel(
            f'<a href="{HF_TOKEN_URL}">Get a token on Hugging Face</a> · '
            f'<a href="{HF_HOME_URL}">huggingface.co</a>',
            self._hf_token_section,
        )
        token_link.setObjectName("hf_token_link")
        token_link.setOpenExternalLinks(True)
        token_link.setTextFormat(Qt.TextFormat.RichText)
        token_layout.addWidget(token_link)

        self._error_status = _hint_label(self, "", object_name="llm_config_error")
        self._error_status.hide()

        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)

        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.addWidget(self._content)
        layout.addWidget(self._error_status)

    def _mode_page(self) -> LlmModePage | None:
        from lexiflow_ui.onboarding.wizard import OnboardingWizard

        wizard = self.wizard()
        if isinstance(wizard, OnboardingWizard):
            return wizard.llm_mode_page
        return None

    def _selected_mode(self) -> LlmMode | None:
        mode_page = self._mode_page()
        if mode_page is None:
            return None
        return mode_page.selected_mode()

    def select_native(self) -> None:
        mode_page = self._mode_page()
        if mode_page is not None:
            mode_page.select_native()

    def select_ollama(self, url: str) -> None:
        mode_page = self._mode_page()
        if mode_page is not None:
            mode_page.select_ollama()
        self._url.setText(url)

    def set_huggingface_token(self, token: str) -> None:
        self._hf_token.setText(token)

    def native_license_steps_text(self) -> str:
        return self._native_license_steps.text()

    def open_native_hub_button(self) -> QPushButton:
        return self._open_native_hub

    def uses_ollama(self) -> bool:
        return self._selected_mode() == LlmMode.OLLAMA

    def uses_native(self) -> bool:
        return self._selected_mode() == LlmMode.NATIVE

    def apply_to_settings(self, settings: Settings) -> Settings:
        token = self._hf_token.text().strip() or None
        if self._selected_mode() == LlmMode.OLLAMA:
            url = self._url.text().strip() or DEFAULT_OLLAMA_URL
            return replace(settings, ollama_url=url, huggingface_token=token)
        return replace(settings, ollama_url=None, huggingface_token=token)

    def initializePage(self) -> None:  # noqa: N802
        from lexiflow_ui.onboarding.wizard import OnboardingWizard

        mode = self._selected_mode()
        if mode is None:
            return

        if mode == LlmMode.NATIVE:
            self.setTitle("Built-in LLM")
            self.setSubTitle(
                "Use llama-server for translate and simplify. "
                "Models load from Hugging Face when needed."
            )
        else:
            self.setTitle("Connect Ollama")
            self.setSubTitle(
                "Point LexiFlow at your Ollama server for translate and simplify."
            )

        self._apply_mode_content(mode)
        if mode == LlmMode.NATIVE:
            self._refresh_native_license_steps()

        wizard = self.wizard()
        if isinstance(wizard, OnboardingWizard):
            if wizard.settings.huggingface_token:
                self._hf_token.setText(wizard.settings.huggingface_token)
            if wizard.settings.ollama_url and mode == LlmMode.OLLAMA:
                self._url.setText(wizard.settings.ollama_url)

        self._clear_error()
        QTimer.singleShot(0, self._resize_wizard_to_content)

    def _clear_content_layout(self) -> None:
        while self._content_layout.count():
            item = self._content_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.hide()

    def _apply_mode_content(self, mode: LlmMode) -> None:
        self._clear_content_layout()
        if mode == LlmMode.NATIVE:
            self._content_layout.addWidget(self._native_panel)
            self._content_layout.addWidget(self._hf_token_section)
            self._native_panel.show()
            self._hf_token_section.show()
            self._ollama_panel.hide()
        else:
            self._content_layout.addWidget(self._ollama_panel)
            self._content_layout.addWidget(self._hf_token_section)
            self._ollama_panel.show()
            self._hf_token_section.show()
            self._native_panel.hide()
        self._content.adjustSize()

    def _resize_wizard_to_content(self) -> None:
        self.adjustSize()
        self._content.adjustSize()
        wizard = self.wizard()
        if wizard is not None:
            wizard.adjustSize()
            hint = wizard.sizeHint()
            wizard.resize(hint.width(), hint.height())

    def nextId(self) -> int:  # noqa: N802
        return TARGET_PAGE_ID

    def previousId(self) -> int:  # noqa: N802
        return LlmModePage.PAGE_ID

    def validatePage(self) -> bool:  # noqa: N802
        from lexiflow_ui.onboarding.wizard import OnboardingWizard

        wizard = self.wizard()
        if not isinstance(wizard, OnboardingWizard):
            return False

        wizard.settings = self.apply_to_settings(wizard.settings)
        if self._selected_mode() == LlmMode.OLLAMA:
            return True
        return self._validate_native_runtime(wizard)

    def _validate_native_runtime(self, wizard: object) -> bool:
        from lexiflow_ui.onboarding.wizard import OnboardingWizard

        if not isinstance(wizard, OnboardingWizard):
            return False
        ready, message = native_llm_operational(wizard.settings)
        if ready:
            self._clear_error()
            return True
        self._show_error(message or "Native LLM is not ready.")
        return False

    def _on_detect(self) -> None:
        url = self._url.text().strip() or DEFAULT_OLLAMA_URL
        if self._probe.is_available(url):
            self._detect_status.setText("Ollama detected at this URL.")
        else:
            self._detect_status.setText(
                "Could not reach Ollama. Start Ollama or check the URL."
            )

    def _refresh_native_license_steps(self) -> None:
        model_url = native_llm_hub_page_url()
        self._native_license_steps.setText(
            "The language model loads from Hugging Face via llama-server "
            f"({model_url}). Embeddings use the pinned MiniLM model from "
            "Hugging Face on first use."
        )

    def _on_open_native_hub(self) -> None:
        open_url(native_llm_hub_page_url())

    def _show_error(self, message: str) -> None:
        self._error_status.setText(message)
        self._error_status.show()

    def _clear_error(self) -> None:
        self._error_status.hide()
        self._error_status.clear()
