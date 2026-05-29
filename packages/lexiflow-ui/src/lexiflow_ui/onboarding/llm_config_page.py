"""Wizard page: configure the LLM / embedding option chosen on LlmModePage."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from lexiflow_core.config.settings import Settings
from lexiflow_core.models.download import (
    ModelAccessError,
    ModelPinError,
    NetworkError,
)
from lexiflow_core.models.model_hints import (
    embedding_import_hint,
    gemma_hub_page_url,
    gemma_import_hint,
)
from lexiflow_core.models.requirements import (
    EMBEDDED_GEMMA_ID,
    EMBEDDING_MINILM_ID,
    required_artifact_ids,
)
from lexiflow_core.models.store import ModelStoreError
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QFileDialog,
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

BOOTSTRAP_PAGE_ID = 4
TARGET_PAGE_ID = 5


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
        self._manual_embedding_dir: Path | None = None
        self._manual_gemma_dir: Path | None = None

        self._content = QWidget(self)
        self._content.setSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum
        )
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setContentsMargins(0, 0, 0, 0)
        self._content_layout.setSpacing(8)
        self._content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        hf_panel = QWidget(self._content)
        hf_layout = QVBoxLayout(hf_panel)
        hf_layout.setContentsMargins(0, 0, 0, 0)
        hf_layout.setSpacing(8)
        self._embedded_note = _hint_label(
            hf_panel,
            "Downloads the pinned embedding model and Gemma. "
            "Requires a large download and at least 8 GiB RAM recommended.",
            object_name="embedded_download_note",
        )
        hf_layout.addWidget(self._embedded_note)
        self._gemma_license_steps = _hint_label(
            hf_panel,
            "",
            object_name="gemma_license_steps",
        )
        hf_layout.addWidget(self._gemma_license_steps)
        self._open_gemma_hub = QPushButton("Open Gemma on Hugging Face", hf_panel)
        self._open_gemma_hub.setObjectName("open_gemma_hub_button")
        self._open_gemma_hub.clicked.connect(self._on_open_gemma_hub)
        hf_layout.addWidget(self._open_gemma_hub)
        self._hf_panel = hf_panel

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
        self._ollama_embed_note = _hint_label(
            ollama_panel,
            "Ollama runs translate and simplify. LexiFlow still downloads the "
            "embedding model from Hugging Face when you continue.",
            object_name="ollama_embedding_note",
        )
        ollama_layout.addWidget(self._ollama_embed_note)
        self._ollama_panel = ollama_panel

        manual_panel = QWidget(self._content)
        manual_layout = QVBoxLayout(manual_panel)
        manual_layout.setContentsMargins(0, 0, 0, 0)
        manual_layout.setSpacing(8)
        self._manual_note = _hint_label(
            manual_panel,
            "Download both models elsewhere, then select each snapshot root "
            "folder here. No network download during setup.",
            object_name="manual_import_note",
        )
        manual_layout.addWidget(self._manual_note)
        self._embedding_hint = _hint_label(
            manual_panel,
            embedding_import_hint(),
            object_name="embedding_import_hint",
        )
        manual_layout.addWidget(self._embedding_hint)
        self._embedding_path = _line_edit(
            manual_panel, placeholder="No folder selected"
        )
        self._embedding_path.setObjectName("embedding_import_path")
        self._embedding_path.setReadOnly(True)
        embedding_browse = QPushButton("Choose embedding folder…", manual_panel)
        embedding_browse.setObjectName("embedding_import_browse")
        embedding_browse.clicked.connect(self._browse_embedding)
        emb_row = QHBoxLayout()
        emb_row.setSpacing(8)
        emb_row.addWidget(self._embedding_path, stretch=1)
        emb_row.addWidget(embedding_browse)
        manual_layout.addLayout(emb_row)
        self._gemma_hint = _hint_label(
            manual_panel,
            gemma_import_hint(),
            object_name="gemma_import_hint",
        )
        manual_layout.addWidget(self._gemma_hint)
        self._gemma_path = _line_edit(manual_panel, placeholder="No folder selected")
        self._gemma_path.setObjectName("gemma_import_path")
        self._gemma_path.setReadOnly(True)
        gemma_browse = QPushButton("Choose Gemma folder…", manual_panel)
        gemma_browse.setObjectName("gemma_import_browse")
        gemma_browse.clicked.connect(self._browse_gemma)
        gem_row = QHBoxLayout()
        gem_row.setSpacing(8)
        gem_row.addWidget(self._gemma_path, stretch=1)
        gem_row.addWidget(gemma_browse)
        manual_layout.addLayout(gem_row)
        self._manual_panel = manual_panel

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
        token_help = _hint_label(
            self._hf_token_section,
            "Use a read token from the same Hugging Face account that accepted "
            "the Gemma license. Optional for public models; required for Gemma.",
            object_name="hf_token_help",
        )
        token_layout.addWidget(token_help)

        self._download_status = _hint_label(
            self, "", object_name="ollama_download_status"
        )
        self._download_status.hide()
        self._download_retry = QPushButton("Retry download", self)
        self._download_retry.setObjectName("ollama_download_retry_button")
        self._download_retry.hide()
        self._download_retry.clicked.connect(self._on_retry_download)

        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)

        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.addWidget(self._content)
        layout.addWidget(self._download_status)
        layout.addWidget(self._download_retry)

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

    def select_embedded(self) -> None:
        mode_page = self._mode_page()
        if mode_page is not None:
            mode_page.select_embedded()

    def select_ollama(self, url: str) -> None:
        mode_page = self._mode_page()
        if mode_page is not None:
            mode_page.select_ollama()
        self._url.setText(url)

    def select_manual_import(
        self,
        *,
        embedding_dir: Path | None = None,
        gemma_dir: Path | None = None,
    ) -> None:
        mode_page = self._mode_page()
        if mode_page is not None:
            mode_page.select_manual_import()
        if embedding_dir is not None:
            self._manual_embedding_dir = embedding_dir
            self._embedding_path.setText(str(embedding_dir))
        if gemma_dir is not None:
            self._manual_gemma_dir = gemma_dir
            self._gemma_path.setText(str(gemma_dir))

    def set_huggingface_token(self, token: str) -> None:
        self._hf_token.setText(token)

    def uses_ollama(self) -> bool:
        return self._selected_mode() == LlmMode.OLLAMA

    def uses_embedded_hf_download(self) -> bool:
        return self._selected_mode() == LlmMode.HF_DOWNLOAD

    def skips_bootstrap_page(self) -> bool:
        mode = self._selected_mode()
        if mode == LlmMode.MANUAL_IMPORT:
            return True
        if mode == LlmMode.HF_DOWNLOAD:
            return False
        return self._all_required_models_installed()

    def _all_required_models_installed(self) -> bool:
        from lexiflow_ui.onboarding.wizard import OnboardingWizard

        wizard = self.wizard()
        if not isinstance(wizard, OnboardingWizard):
            return False
        settings = self.apply_to_settings(wizard.settings)
        store = wizard.bootstrap_page.model_store
        return all(
            store.is_installed(artifact_id)
            for artifact_id in required_artifact_ids(settings)
        )

    def download_status_text(self) -> str:
        return self._download_status.text()

    def download_retry_button(self) -> QPushButton:
        return self._download_retry

    def open_gemma_hub_button(self) -> QPushButton:
        return self._open_gemma_hub

    def gemma_license_steps_text(self) -> str:
        return self._gemma_license_steps.text()

    def is_download_status_visible(self) -> bool:
        return self._download_status.isVisible()

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

        titles = {
            LlmMode.HF_DOWNLOAD: (
                "Download from Hugging Face",
                "Accept the Gemma license on Hugging Face first, then continue.",
            ),
            LlmMode.OLLAMA: (
                "Connect Ollama",
                "Point LexiFlow at your Ollama server for translate and simplify.",
            ),
            LlmMode.MANUAL_IMPORT: (
                "Import model folders",
                "Select local folders for the embedding model and Gemma.",
            ),
        }
        title, subtitle = titles[mode]
        self.setTitle(title)
        self.setSubTitle(subtitle)

        self._apply_mode_content(mode)
        if mode == LlmMode.HF_DOWNLOAD:
            self._refresh_gemma_license_steps()

        wizard = self.wizard()
        if isinstance(wizard, OnboardingWizard):
            if wizard.settings.huggingface_token:
                self._hf_token.setText(wizard.settings.huggingface_token)
            if wizard.settings.ollama_url and mode == LlmMode.OLLAMA:
                self._url.setText(wizard.settings.ollama_url)

        self._clear_download_error()
        QTimer.singleShot(0, self._resize_wizard_to_content)

    def _clear_content_layout(self) -> None:
        while self._content_layout.count():
            item = self._content_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.hide()

    def _apply_mode_content(self, mode: LlmMode) -> None:
        self._clear_content_layout()
        if mode == LlmMode.HF_DOWNLOAD:
            self._content_layout.addWidget(self._hf_panel)
            self._content_layout.addWidget(self._hf_token_section)
            self._hf_panel.show()
            self._hf_token_section.show()
            self._ollama_panel.hide()
            self._manual_panel.hide()
        elif mode == LlmMode.OLLAMA:
            self._content_layout.addWidget(self._ollama_panel)
            self._content_layout.addWidget(self._hf_token_section)
            self._ollama_panel.show()
            self._hf_token_section.show()
            self._hf_panel.hide()
            self._manual_panel.hide()
        else:
            self._content_layout.addWidget(self._manual_panel)
            self._manual_panel.show()
            self._hf_panel.hide()
            self._ollama_panel.hide()
            self._hf_token_section.hide()
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
        if self.skips_bootstrap_page():
            return TARGET_PAGE_ID
        return BOOTSTRAP_PAGE_ID

    def previousId(self) -> int:  # noqa: N802
        return LlmModePage.PAGE_ID

    def validatePage(self) -> bool:  # noqa: N802
        from lexiflow_ui.onboarding.wizard import OnboardingWizard

        wizard = self.wizard()
        if not isinstance(wizard, OnboardingWizard):
            return False

        wizard.settings = self.apply_to_settings(wizard.settings)
        store = wizard.bootstrap_page.model_store
        store.set_huggingface_token(wizard.settings.huggingface_token)

        mode = self._selected_mode()
        if mode == LlmMode.MANUAL_IMPORT:
            return self._validate_manual_import(store)
        return True

    def _validate_manual_import(self, store: object) -> bool:
        from lexiflow_core.models.store import ModelStore

        if not isinstance(store, ModelStore):
            return False
        if self._manual_embedding_dir is None or self._manual_gemma_dir is None:
            self._show_download_error(
                "Select both the embedding model folder and the Gemma folder."
            )
            return False
        self._clear_download_error()
        try:
            store.import_from_directory(EMBEDDING_MINILM_ID, self._manual_embedding_dir)
            store.import_from_directory(EMBEDDED_GEMMA_ID, self._manual_gemma_dir)
        except ModelStoreError as exc:
            self._show_download_error(str(exc))
            return False
        return True

    def _download_embedding_for_ollama(self, store: object, settings: Settings) -> bool:
        from lexiflow_core.models.store import ModelStore

        if not isinstance(store, ModelStore):
            return False
        self._clear_download_error()
        required = required_artifact_ids(settings)
        try:
            for artifact_id in required:
                store.ensure_installed(artifact_id, on_progress=lambda _v: None)
        except ModelPinError:
            self._show_download_error(
                "Model manifest pin is invalid. Update LexiFlow or report a bug."
            )
            return False
        except ModelAccessError:
            self._show_download_error(
                "Embedding download requires Hugging Face access. "
                "Add a token above, then retry. "
                "Ollama is only used for the LLM; embeddings still come from "
                "Hugging Face."
            )
            return False
        except NetworkError:
            self._show_download_error(
                "Embedding model download failed. Check your network and retry. "
                "Ollama is connected for the LLM; embeddings are downloaded "
                "separately from Hugging Face."
            )
            return False
        except ModelStoreError as exc:
            self._show_download_error(str(exc))
            return False
        return True

    def _on_detect(self) -> None:
        url = self._url.text().strip() or DEFAULT_OLLAMA_URL
        if self._probe.is_available(url):
            self._detect_status.setText("Ollama detected at this URL.")
        else:
            self._detect_status.setText(
                "Could not reach Ollama. Start Ollama or check the URL."
            )

    def _browse_embedding(self) -> None:
        path = QFileDialog.getExistingDirectory(
            self,
            "Select embedding model folder",
            str(self._manual_embedding_dir or Path.home()),
        )
        if path:
            self._manual_embedding_dir = Path(path)
            self._embedding_path.setText(path)

    def _browse_gemma(self) -> None:
        path = QFileDialog.getExistingDirectory(
            self,
            "Select Gemma model folder",
            str(self._manual_gemma_dir or Path.home()),
        )
        if path:
            self._manual_gemma_dir = Path(path)
            self._gemma_path.setText(path)

    def _refresh_gemma_license_steps(self) -> None:
        gemma_url = gemma_hub_page_url()
        self._gemma_license_steps.setText(
            "Before you continue:\n"
            "1. Log in at huggingface.co with the same account as your token below.\n"
            "2. Open the Gemma model page and accept the license (once per account).\n"
            f"   {gemma_url}\n"
            "3. On the next step, LexiFlow downloads pinned MiniLM and Gemma."
        )

    def _on_open_gemma_hub(self) -> None:
        open_url(gemma_hub_page_url())

    def _on_retry_download(self) -> None:
        from lexiflow_ui.onboarding.wizard import OnboardingWizard

        wizard = self.wizard()
        if not isinstance(wizard, OnboardingWizard):
            return
        wizard.settings = self.apply_to_settings(wizard.settings)
        store = wizard.bootstrap_page.model_store
        store.set_huggingface_token(wizard.settings.huggingface_token)
        if self._download_embedding_for_ollama(store, wizard.settings):
            self._clear_download_error()
            self.completeChanged.emit()

    def _show_download_error(self, message: str) -> None:
        self._download_status.setText(message)
        self._download_status.show()
        self._download_retry.show()

    def _clear_download_error(self) -> None:
        self._download_status.hide()
        self._download_retry.hide()
        self._download_status.clear()
