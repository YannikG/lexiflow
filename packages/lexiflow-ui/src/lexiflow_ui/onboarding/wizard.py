"""First-run onboarding wizard."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from lexiflow_core.config.settings import Settings
from lexiflow_core.config.settings_store import SettingsStore
from lexiflow_core.languages.models import CEFRLevel
from lexiflow_core.languages.setup import (
    complete_language_onboarding,
    finalize_onboarding,
)
from lexiflow_core.models.store import ModelStore
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import (
    QComboBox,
    QLabel,
    QVBoxLayout,
    QWizard,
    QWizardPage,
)

from lexiflow_ui.onboarding.llm_config_page import LlmConfigPage
from lexiflow_ui.onboarding.llm_mode_page import LlmModePage
from lexiflow_ui.onboarding.model_bootstrap_page import ModelBootstrapPage
from lexiflow_ui.onboarding.ollama_probe import OllamaProbe
from lexiflow_ui.onboarding.system_info import SystemInfo, ram_warning_message
from lexiflow_ui.widgets.catalog_picker import CatalogPickerWidget


class WelcomePage(QWizardPage):
    def __init__(
        self,
        *,
        system_info: SystemInfo,
        parent: QWizardPage | None = None,
    ) -> None:
        super().__init__(parent)
        self.setTitle("Welcome to LexiFlow")
        self.setSubTitle("Set up your languages to start learning.")
        layout = QVBoxLayout(self)
        self._ram_warning = QLabel(self)
        self._ram_warning.setObjectName("ram_warning")
        self._ram_warning.setWordWrap(True)
        self._ram_warning.hide()
        layout.addWidget(self._ram_warning)
        layout.addStretch()
        warning = ram_warning_message(system_info.total_ram_bytes())
        if warning is not None:
            self._ram_warning.setText(warning)
            self._ram_warning.show()

    def ram_warning_label(self) -> QLabel:
        return self._ram_warning


class NativeLanguagePage(QWizardPage):
    def __init__(self, parent: QWizardPage | None = None) -> None:
        super().__init__(parent)
        self.setTitle("Native language")
        self.setSubTitle("Choose the language you use for explanations.")
        self._picker = CatalogPickerWidget(self)
        self._picker.setObjectName("native_language_picker")
        layout = QVBoxLayout(self)
        layout.addWidget(self._picker)

    def select_language(self, iso: str) -> None:
        self._picker.set_selected_iso(iso)

    def selected_language(self) -> str | None:
        return self._picker.selected_iso()

    def validatePage(self) -> bool:  # noqa: N802
        return self.selected_language() is not None


class TargetLanguagePage(QWizardPage):
    def __init__(self, parent: QWizardPage | None = None) -> None:
        super().__init__(parent)
        self.setTitle("Target language")
        self.setSubTitle(
            "Choose the language you want to learn and your current level."
        )
        self._picker = CatalogPickerWidget(self)
        self._picker.setObjectName("target_language_picker")
        self._level = QComboBox(self)
        self._level.setObjectName("target_level_combo")
        for level in CEFRLevel:
            self._level.addItem(level.value, level)
        layout = QVBoxLayout(self)
        layout.addWidget(self._picker)
        layout.addWidget(QLabel("Your current level", self))
        layout.addWidget(self._level)

    def select_language(self, iso: str) -> None:
        self._picker.set_selected_iso(iso)

    def select_level(self, level: str) -> None:
        self._level.setCurrentText(level)

    def selected_language(self) -> str | None:
        return self._picker.selected_iso()

    def selected_level(self) -> CEFRLevel:
        value = self._level.currentData()
        if isinstance(value, CEFRLevel):
            return value
        return CEFRLevel(self._level.currentText())

    def validatePage(self) -> bool:  # noqa: N802
        target_iso = self.selected_language()
        if target_iso is None:
            return False
        wizard = self.wizard()
        if isinstance(wizard, OnboardingWizard):
            native_iso = wizard.native_page.selected_language()
            if native_iso is not None and native_iso == target_iso:
                return False
        return True

    def previousId(self) -> int:  # noqa: N802
        wizard = self.wizard()
        skips_bootstrap = (
            isinstance(wizard, OnboardingWizard)
            and wizard.llm_page.skips_bootstrap_page()
        )
        if skips_bootstrap:
            return LlmConfigPage.PAGE_ID
        return 4


class OnboardingWizard(QWizard):
    def __init__(
        self,
        *,
        data_root: Path,
        settings_store: SettingsStore,
        settings: Settings,
        system_info: SystemInfo | None = None,
        model_store: ModelStore | None = None,
        ollama_probe: OllamaProbe | None = None,
        parent: QWizard | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("onboarding_wizard")
        self.setWindowTitle("LexiFlow Setup")
        self.setWizardStyle(QWizard.WizardStyle.ModernStyle)
        self._data_root = data_root
        self._settings_store = settings_store
        self._settings = settings
        store = (
            model_store
            if model_store is not None
            else _default_model_store(data_root, settings)
        )
        info = system_info if system_info is not None else _default_system_info()
        self._welcome = WelcomePage(
            system_info=info,
            parent=self,
        )
        self._native = NativeLanguagePage(parent=self)
        self._llm_mode = LlmModePage(parent=self)
        self._llm_config = LlmConfigPage(ollama_probe=ollama_probe, parent=self)
        self._bootstrap = ModelBootstrapPage(model_store=store, parent=self)
        self._target = TargetLanguagePage(parent=self)
        self.setPage(0, self._welcome)
        self.setPage(1, self._native)
        self.setPage(LlmModePage.PAGE_ID, self._llm_mode)
        self.setPage(LlmConfigPage.PAGE_ID, self._llm_config)
        self.setPage(4, self._bootstrap)
        self.setPage(5, self._target)
        self.finished.connect(self._on_finished)

    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802
        self._bootstrap._stop_worker()
        super().closeEvent(event)

    @property
    def settings(self) -> Settings:
        return self._settings

    @settings.setter
    def settings(self, value: Settings) -> None:
        self._settings = value

    @property
    def welcome_page(self) -> WelcomePage:
        return self._welcome

    @property
    def native_page(self) -> NativeLanguagePage:
        return self._native

    @property
    def llm_mode_page(self) -> LlmModePage:
        return self._llm_mode

    @property
    def llm_page(self) -> LlmConfigPage:
        """Configuration form for the chosen LLM mode (page 3)."""
        return self._llm_config

    @property
    def bootstrap_page(self) -> ModelBootstrapPage:
        return self._bootstrap

    @property
    def target_page(self) -> TargetLanguagePage:
        return self._target

    def _on_finished(self, result: int) -> None:
        if result != int(QWizard.DialogCode.Accepted):
            return
        native_iso = self._native.selected_language()
        target_iso = self._target.selected_language()
        if native_iso is None or target_iso is None:
            return
        self._settings = complete_language_onboarding(
            data_root=self._data_root,
            settings_store=self._settings_store,
            settings=self._settings,
            native_language=native_iso,
            target_language=target_iso,
            level=self._target.selected_level(),
        )
        self._settings = finalize_onboarding(
            settings_store=self._settings_store,
            settings=self._settings,
        )


def _default_system_info() -> SystemInfo:
    from lexiflow_ui.onboarding.system_info import PlatformSystemInfo

    return PlatformSystemInfo()


def _default_model_store(data_root: Path, settings: Settings) -> ModelStore:
    from lexiflow_core.models.download import default_model_downloader
    from lexiflow_core.models.store import ModelStore

    return ModelStore(
        data_root,
        downloader=default_model_downloader(),
        huggingface_token=settings.huggingface_token,
    )


def run_onboarding_if_needed(
    *,
    data_root: Path,
    settings_store: SettingsStore,
    settings: Settings,
    system_info: SystemInfo | None = None,
    wizard_factory: Callable[..., OnboardingWizard] | None = None,
) -> Settings | None:
    """Show onboarding when incomplete. Returns None if the user cancels."""
    if settings.onboarding_complete:
        return settings
    factory = wizard_factory if wizard_factory is not None else OnboardingWizard
    wizard = factory(
        data_root=data_root,
        settings_store=settings_store,
        settings=settings,
        system_info=system_info,
    )
    result = wizard.exec()
    if result != int(QWizard.DialogCode.Accepted):
        return None
    return wizard.settings
