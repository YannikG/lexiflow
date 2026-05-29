"""First-run onboarding wizard."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from lexiflow_core.config.settings import Settings
from lexiflow_core.config.settings_store import SettingsStore
from lexiflow_core.languages.models import CEFRLevel
from PySide6.QtWidgets import (
    QComboBox,
    QLabel,
    QVBoxLayout,
    QWizard,
    QWizardPage,
)

from lexiflow_ui.onboarding.completion import complete_onboarding
from lexiflow_ui.onboarding.system_info import RECOMMENDED_RAM_BYTES, SystemInfo
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
        total_ram = system_info.total_ram_bytes()
        if total_ram < RECOMMENDED_RAM_BYTES:
            gib = total_ram / (1024**3)
            self._ram_warning.setText(
                f"Your system reports about {gib:.1f} GiB of RAM. "
                "LexiFlow recommends at least 8 GiB for local models. "
                "You can continue anyway."
            )
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


class OnboardingWizard(QWizard):
    def __init__(
        self,
        *,
        data_root: Path,
        settings_store: SettingsStore,
        settings: Settings,
        system_info: SystemInfo | None = None,
        parent: QWizard | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("onboarding_wizard")
        self.setWindowTitle("LexiFlow Setup")
        self.setWizardStyle(QWizard.WizardStyle.ModernStyle)
        self._data_root = data_root
        self._settings_store = settings_store
        self._settings = settings
        info = system_info if system_info is not None else _default_system_info()
        self._welcome = WelcomePage(
            system_info=info,
            parent=self,
        )
        self._native = NativeLanguagePage(parent=self)
        self._target = TargetLanguagePage(parent=self)
        self.setPage(0, self._welcome)
        self.setPage(1, self._native)
        self.setPage(2, self._target)
        self.finished.connect(self._on_finished)

    @property
    def welcome_page(self) -> WelcomePage:
        return self._welcome

    @property
    def native_page(self) -> NativeLanguagePage:
        return self._native

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
        self._settings = complete_onboarding(
            data_root=self._data_root,
            settings_store=self._settings_store,
            settings=self._settings,
            native_language=native_iso,
            target_language=target_iso,
            level=self._target.selected_level(),
        )

    @property
    def settings(self) -> Settings:
        return self._settings


def _default_system_info() -> SystemInfo:
    from lexiflow_ui.onboarding.system_info import PlatformSystemInfo

    return PlatformSystemInfo()


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
