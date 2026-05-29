"""Onboarding wizard and app gate tests."""

from __future__ import annotations

from pathlib import Path

from lexiflow_core.config.settings import Settings
from lexiflow_core.config.settings_store import SettingsStore
from lexiflow_ui.app import run
from lexiflow_ui.main_window import MainWindow
from lexiflow_ui.onboarding.wizard import OnboardingWizard, run_onboarding_if_needed
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QApplication, QWizard


class _SmokeInstanceGuard:
    def try_acquire(self) -> bool:
        return True

    def handle_secondary_launch(self) -> int:
        return 0

    def listen_for_activation(self, _callback: object) -> None:
        return None

    def release(self) -> None:
        return None


class FakeSystemInfo:
    def __init__(self, total_ram_bytes: int) -> None:
        self._total_ram_bytes = total_ram_bytes

    def total_ram_bytes(self) -> int:
        return self._total_ram_bytes


def _advance_wizard_to_finish(wizard: OnboardingWizard, qtbot) -> None:
    wizard.next()
    qtbot.wait(10)
    wizard.native_page.select_language("en")
    wizard.next()
    qtbot.wait(10)
    wizard.target_page.select_language("es")
    wizard.target_page.select_level("A2")
    finish = wizard.button(QWizard.WizardButton.FinishButton)
    qtbot.mouseClick(finish, Qt.MouseButton.LeftButton)
    qtbot.wait(10)


def test_onboarding_flag_blocks_main_window(qtbot, monkeypatch, tmp_path: Path) -> None:
    config_dir = tmp_path / "config"
    data_root = tmp_path / "library"
    store = SettingsStore(config_dir=config_dir)
    store.save(Settings(data_root=data_root, onboarding_complete=False))
    main_windows: list[MainWindow] = []
    wizard_instances: list[OnboardingWizard] = []

    original_show = MainWindow.show

    def track_main_show(self: MainWindow) -> None:
        main_windows.append(self)
        original_show(self)

    def reject_wizard(self: OnboardingWizard) -> int:
        wizard_instances.append(self)
        qtbot.addWidget(self)
        QTimer.singleShot(0, self.reject)
        app = QApplication.instance()
        assert app is not None
        QTimer.singleShot(0, app.quit)
        return int(QWizard.DialogCode.Rejected)

    monkeypatch.setattr(MainWindow, "show", track_main_show)
    monkeypatch.setattr(OnboardingWizard, "exec", reject_wizard)

    exit_code = run(
        argv=["lexiflow-test"],
        settings_store=store,
        instance_guard=_SmokeInstanceGuard(),
    )

    assert exit_code == 0
    assert wizard_instances
    assert not main_windows


def test_completing_onboarding_sets_flag(qtbot, tmp_path: Path) -> None:
    config_dir = tmp_path / "config"
    data_root = tmp_path / "library"
    store = SettingsStore(config_dir=config_dir)
    settings = Settings(data_root=data_root, onboarding_complete=False)

    wizard = OnboardingWizard(
        data_root=data_root,
        settings_store=store,
        settings=settings,
        system_info=FakeSystemInfo(16 * 1024**3),
    )
    qtbot.addWidget(wizard)
    wizard.show()
    _advance_wizard_to_finish(wizard, qtbot)

    loaded = store.load()
    assert loaded.onboarding_complete is True
    assert loaded.native_language == "en"
    assert loaded.active_target_language == "es"


def test_ram_warn_below_threshold_is_visible(qtbot) -> None:
    wizard = OnboardingWizard(
        data_root=Path("/tmp/unused"),
        settings_store=SettingsStore(config_dir=Path("/tmp/unused-config")),
        settings=Settings(),
        system_info=FakeSystemInfo(4 * 1024**3),
    )
    qtbot.addWidget(wizard)
    wizard.show()
    warning = wizard.welcome_page.ram_warning_label()
    assert warning.text()
    assert "4.0 GiB" in warning.text()
    assert "continue anyway" in warning.text().lower()


def test_ram_unknown_shows_detection_message(qtbot) -> None:
    wizard = OnboardingWizard(
        data_root=Path("/tmp/unused"),
        settings_store=SettingsStore(config_dir=Path("/tmp/unused-config")),
        settings=Settings(),
        system_info=FakeSystemInfo(0),
    )
    qtbot.addWidget(wizard)
    wizard.show()
    warning = wizard.welcome_page.ram_warning_label()
    assert "could not detect" in warning.text().lower()
    assert "0.0 GiB" not in warning.text()


def test_low_ram_warning_allows_wizard_finish(qtbot, tmp_path: Path) -> None:
    config_dir = tmp_path / "config"
    data_root = tmp_path / "library"
    store = SettingsStore(config_dir=config_dir)
    settings = Settings(data_root=data_root, onboarding_complete=False)

    wizard = OnboardingWizard(
        data_root=data_root,
        settings_store=store,
        settings=settings,
        system_info=FakeSystemInfo(4 * 1024**3),
    )
    qtbot.addWidget(wizard)
    wizard.show()
    _advance_wizard_to_finish(wizard, qtbot)

    assert store.load().onboarding_complete is True


def test_target_language_rejects_same_as_native(qtbot, tmp_path: Path) -> None:
    config_dir = tmp_path / "config"
    data_root = tmp_path / "library"
    store = SettingsStore(config_dir=config_dir)
    wizard = OnboardingWizard(
        data_root=data_root,
        settings_store=store,
        settings=Settings(data_root=data_root),
        system_info=FakeSystemInfo(16 * 1024**3),
    )
    qtbot.addWidget(wizard)
    wizard.show()
    wizard.next()
    qtbot.wait(10)
    wizard.native_page.select_language("en")
    wizard.next()
    qtbot.wait(10)
    wizard.target_page.select_language("en")

    assert wizard.target_page.validatePage() is False


def test_toolbar_shows_active_language_and_level(qtbot, tmp_path: Path) -> None:
    from lexiflow_ui.worker_supervisor import WorkerSupervisor

    config_dir = tmp_path / "config"
    data_root = tmp_path / "library"
    store = SettingsStore(config_dir=config_dir)
    settings = Settings(data_root=data_root, onboarding_complete=False)
    wizard = OnboardingWizard(
        data_root=data_root,
        settings_store=store,
        settings=settings,
        system_info=FakeSystemInfo(16 * 1024**3),
    )
    qtbot.addWidget(wizard)
    wizard.show()
    _advance_wizard_to_finish(wizard, qtbot)

    loaded = store.load()
    assert loaded.active_target_language == "es"
    supervisor = WorkerSupervisor(data_root=data_root)
    window = MainWindow(supervisor=supervisor, settings=loaded, data_root=data_root)
    qtbot.addWidget(window)

    widget = window.active_target_language
    assert widget is not None
    label = widget.label().text()
    assert "A2" in label
    assert "Spanish" in label


def test_active_target_language_shows_fallback_for_invalid_iso(
    qtbot, tmp_path: Path
) -> None:
    from lexiflow_ui.widgets.active_target_language import ActiveTargetLanguageWidget

    widget = ActiveTargetLanguageWidget(
        settings=Settings(active_target_language="ru"),
        data_root=tmp_path / "library",
    )
    qtbot.addWidget(widget)

    assert widget.label().text() == "Language: ru"


def test_run_onboarding_if_needed_skips_when_complete(tmp_path: Path) -> None:
    config_dir = tmp_path / "config"
    data_root = tmp_path / "library"
    store = SettingsStore(config_dir=config_dir)
    settings = Settings(data_root=data_root, onboarding_complete=True)

    result = run_onboarding_if_needed(
        data_root=data_root,
        settings_store=store,
        settings=settings,
    )

    assert result == settings
