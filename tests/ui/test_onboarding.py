"""Onboarding wizard and app gate tests."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from lexiflow_core.config.settings import Settings
from lexiflow_core.config.settings_store import SettingsStore
from lexiflow_core.models.download import FakeModelDownloader
from lexiflow_core.models.lockfile import load_models_lock
from lexiflow_core.models.model_hints import native_llm_hub_page_url
from lexiflow_core.models.store import ModelStore
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


class RecordingFakeDownloader:
    """Records each artifact id passed to download()."""

    def __init__(self) -> None:
        self.artifact_ids: list[str] = []

    def download(
        self,
        artifact: object,
        dest: Path,
        *,
        token: str | None,
        on_progress: object = None,
        on_log_line: object = None,
    ) -> None:
        from lexiflow_core.models.lockfile import ModelArtifact

        assert isinstance(artifact, ModelArtifact)
        del token
        if on_log_line is not None:
            on_log_line(f"Downloading {artifact.id}:  50%|████     | 1/2")
        if on_progress is not None:
            on_progress(0.5)
            on_progress(1.0)
        self.artifact_ids.append(artifact.id)
        dest.mkdir(parents=True, exist_ok=True)
        (dest / "revision.txt").write_text(artifact.revision, encoding="utf-8")


def _make_model_store(
    data_root: Path, *, downloader: FakeModelDownloader | RecordingFakeDownloader
) -> ModelStore:
    return ModelStore(
        data_root,
        lock=load_models_lock(),
        downloader=downloader,
    )


def _advance_wizard_to_finish(
    wizard: OnboardingWizard,
    qtbot,
    *,
    use_ollama: bool = False,
) -> None:
    wizard.next()
    qtbot.wait(10)
    wizard.native_page.select_language("en")
    wizard.next()
    qtbot.wait(10)
    wizard.next()
    qtbot.wait(10)
    if use_ollama:
        wizard.llm_mode_page.select_ollama()
    wizard.next()
    qtbot.wait(10)
    if use_ollama:
        wizard.llm_page.select_ollama("http://127.0.0.1:11434")
    wizard.next()
    qtbot.wait(50)
    wizard.target_page.select_language("es")
    wizard.target_page.select_level("A2")
    finish = wizard.button(QWizard.WizardButton.FinishButton)
    qtbot.mouseClick(finish, Qt.MouseButton.LeftButton)
    qtbot.wait(10)


def _wizard_factory(model_store: ModelStore):
    def factory(
        *,
        data_root: Path,
        settings_store: SettingsStore,
        settings: Settings,
        system_info: FakeSystemInfo | None = None,
    ) -> OnboardingWizard:
        return OnboardingWizard(
            data_root=data_root,
            settings_store=settings_store,
            settings=settings,
            system_info=system_info,
            model_store=model_store,
        )

    return factory


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


def test_re_run_onboarding_after_resetting_complete_flag(qtbot, tmp_path: Path) -> None:
    """Finishing the wizard twice must set onboarding_complete when target exists."""
    config_dir = tmp_path / "config"
    data_root = tmp_path / "library"
    store = SettingsStore(config_dir=config_dir)
    settings = Settings(data_root=data_root, onboarding_complete=False)
    model_store = _make_model_store(data_root, downloader=FakeModelDownloader())

    wizard = OnboardingWizard(
        data_root=data_root,
        settings_store=store,
        settings=settings,
        system_info=FakeSystemInfo(16 * 1024**3),
        model_store=model_store,
    )
    qtbot.addWidget(wizard)
    wizard.show()
    _advance_wizard_to_finish(wizard, qtbot)
    assert store.load().onboarding_complete is True

    wizard.bootstrap_page._stop_worker()
    wizard.close()
    qtbot.wait(50)

    store.save(replace(store.load(), onboarding_complete=False))

    wizard_again = OnboardingWizard(
        data_root=data_root,
        settings_store=store,
        settings=store.load(),
        system_info=FakeSystemInfo(16 * 1024**3),
        model_store=model_store,
    )
    qtbot.addWidget(wizard_again)
    wizard_again.show()
    _advance_wizard_to_finish(wizard_again, qtbot)

    loaded = store.load()
    assert loaded.onboarding_complete is True
    assert loaded.native_language == "en"
    assert loaded.active_target_language == "es"


def test_completing_onboarding_sets_flag(qtbot, tmp_path: Path) -> None:
    config_dir = tmp_path / "config"
    data_root = tmp_path / "library"
    store = SettingsStore(config_dir=config_dir)
    settings = Settings(data_root=data_root, onboarding_complete=False)

    downloader = FakeModelDownloader()
    wizard = OnboardingWizard(
        data_root=data_root,
        settings_store=store,
        settings=settings,
        system_info=FakeSystemInfo(16 * 1024**3),
        model_store=_make_model_store(data_root, downloader=downloader),
    )
    qtbot.addWidget(wizard)
    wizard.show()
    _advance_wizard_to_finish(wizard, qtbot)

    loaded = store.load()
    assert loaded.onboarding_complete is True
    assert downloader.call_count == 0
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
        model_store=_make_model_store(data_root, downloader=FakeModelDownloader()),
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
        model_store=_make_model_store(data_root, downloader=FakeModelDownloader()),
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


def test_ollama_path_skips_bootstrap_and_completes(qtbot, tmp_path: Path) -> None:
    """Ollama path goes straight to target language; no model downloads."""
    config_dir = tmp_path / "config"
    data_root = tmp_path / "library"
    store = SettingsStore(config_dir=config_dir)
    settings = Settings(data_root=data_root, onboarding_complete=False)
    downloader = RecordingFakeDownloader()
    wizard = OnboardingWizard(
        data_root=data_root,
        settings_store=store,
        settings=settings,
        system_info=FakeSystemInfo(16 * 1024**3),
        model_store=_make_model_store(data_root, downloader=downloader),
    )
    qtbot.addWidget(wizard)
    wizard.show()
    wizard.next()
    qtbot.wait(10)
    wizard.native_page.select_language("en")
    wizard.next()
    qtbot.wait(10)
    wizard.llm_mode_page.select_ollama()
    wizard.next()
    qtbot.wait(10)
    wizard.llm_page.select_ollama("http://127.0.0.1:11434")
    assert wizard.llm_page.uses_ollama()
    assert wizard.llm_page.nextId() == 5

    wizard.next()
    qtbot.wait(50)
    assert wizard.currentPage() is wizard.target_page
    assert downloader.artifact_ids == []

    wizard.target_page.select_language("es")
    wizard.target_page.select_level("A2")
    finish = wizard.button(QWizard.WizardButton.FinishButton)
    qtbot.mouseClick(finish, Qt.MouseButton.LeftButton)
    qtbot.wait(10)

    loaded = store.load()
    assert loaded.onboarding_complete is True
    assert loaded.ollama_url == "http://127.0.0.1:11434"


def test_native_path_skips_bootstrap_page(qtbot, tmp_path: Path) -> None:
    config_dir = tmp_path / "config"
    data_root = tmp_path / "library"
    store = SettingsStore(config_dir=config_dir)
    settings = Settings(data_root=data_root, onboarding_complete=False)
    downloader = RecordingFakeDownloader()
    wizard = OnboardingWizard(
        data_root=data_root,
        settings_store=store,
        settings=settings,
        system_info=FakeSystemInfo(16 * 1024**3),
        model_store=_make_model_store(data_root, downloader=downloader),
    )
    qtbot.addWidget(wizard)
    wizard.show()
    wizard.next()
    qtbot.wait(10)
    wizard.native_page.select_language("en")
    wizard.next()
    qtbot.wait(10)
    wizard.llm_mode_page.select_embedded()
    wizard.next()
    qtbot.wait(10)
    assert wizard.llm_page.nextId() == 5

    wizard.next()
    qtbot.wait(50)
    assert wizard.currentPage() is wizard.target_page
    assert downloader.artifact_ids == []


def test_ollama_path_skips_bootstrap_page(qtbot, tmp_path: Path) -> None:
    config_dir = tmp_path / "config"
    data_root = tmp_path / "library"
    store = SettingsStore(config_dir=config_dir)
    settings = Settings(data_root=data_root, onboarding_complete=False)
    downloader = FakeModelDownloader()
    wizard = OnboardingWizard(
        data_root=data_root,
        settings_store=store,
        settings=settings,
        system_info=FakeSystemInfo(16 * 1024**3),
        model_store=_make_model_store(data_root, downloader=downloader),
    )
    qtbot.addWidget(wizard)
    wizard.show()
    wizard.next()
    qtbot.wait(10)
    wizard.native_page.select_language("en")
    wizard.next()
    qtbot.wait(10)
    wizard.llm_mode_page.select_ollama()
    wizard.next()
    qtbot.wait(10)
    wizard.llm_page.select_ollama("http://127.0.0.1:11434")
    assert wizard.llm_page.nextId() == 5
    wizard.next()
    qtbot.wait(50)

    assert wizard.currentId() == 5
    assert downloader.call_count == 0


def test_ollama_onboarding_does_not_download_models(qtbot, tmp_path: Path) -> None:
    config_dir = tmp_path / "config"
    data_root = tmp_path / "library"
    store = SettingsStore(config_dir=config_dir)
    settings = Settings(data_root=data_root, onboarding_complete=False)
    downloader = FakeModelDownloader()
    wizard = OnboardingWizard(
        data_root=data_root,
        settings_store=store,
        settings=settings,
        system_info=FakeSystemInfo(16 * 1024**3),
        model_store=_make_model_store(data_root, downloader=downloader),
    )
    qtbot.addWidget(wizard)
    wizard.show()
    _advance_wizard_to_finish(wizard, qtbot, use_ollama=True)

    assert downloader.call_count == 0
    assert store.load().ollama_url == "http://127.0.0.1:11434"


def test_native_config_page_shows_model_guidance(qtbot, tmp_path: Path) -> None:
    config_dir = tmp_path / "config"
    data_root = tmp_path / "library"
    store = SettingsStore(config_dir=config_dir)
    settings = Settings(data_root=data_root, onboarding_complete=False)
    wizard = OnboardingWizard(
        data_root=data_root,
        settings_store=store,
        settings=settings,
        system_info=FakeSystemInfo(16 * 1024**3),
        model_store=_make_model_store(data_root, downloader=FakeModelDownloader()),
    )
    qtbot.addWidget(wizard)
    wizard.show()
    wizard.next()
    qtbot.wait(10)
    wizard.native_page.select_language("en")
    wizard.next()
    qtbot.wait(10)
    wizard.llm_mode_page.select_embedded()
    wizard.next()
    qtbot.wait(10)

    steps_text = wizard.llm_page.native_license_steps_text()
    assert native_llm_hub_page_url() in steps_text
    assert wizard.llm_page.open_native_hub_button().isVisible()
    assert "hugging face" in wizard.llm_page.subTitle().lower()


def test_native_config_blocks_when_llama_server_missing(qtbot, tmp_path: Path) -> None:
    config_dir = tmp_path / "config"
    data_root = tmp_path / "library"
    store = SettingsStore(config_dir=config_dir)
    settings = Settings(data_root=data_root, onboarding_complete=False)

    def _not_ready(settings: Settings) -> tuple[bool, str | None]:
        return False, "Install llama-server from llama.cpp."

    import lexiflow_ui.onboarding.llm_config_page as llm_config_page

    original = llm_config_page.native_llm_operational
    llm_config_page.native_llm_operational = _not_ready
    try:
        wizard = OnboardingWizard(
            data_root=data_root,
            settings_store=store,
            settings=settings,
            system_info=FakeSystemInfo(16 * 1024**3),
            model_store=_make_model_store(data_root, downloader=FakeModelDownloader()),
        )
        qtbot.addWidget(wizard)
        wizard.show()
        wizard.next()
        qtbot.wait(10)
        wizard.native_page.select_language("en")
        wizard.next()
        qtbot.wait(10)
        wizard.llm_mode_page.select_native()
        wizard.next()
        qtbot.wait(10)

        assert wizard.llm_page.validatePage() is False
    finally:
        llm_config_page.native_llm_operational = original


def test_llm_page_persists_huggingface_token(qtbot, tmp_path: Path) -> None:
    config_dir = tmp_path / "config"
    data_root = tmp_path / "library"
    store = SettingsStore(config_dir=config_dir)
    settings = Settings(data_root=data_root, onboarding_complete=False)
    wizard = OnboardingWizard(
        data_root=data_root,
        settings_store=store,
        settings=settings,
        system_info=FakeSystemInfo(16 * 1024**3),
        model_store=_make_model_store(data_root, downloader=FakeModelDownloader()),
    )
    qtbot.addWidget(wizard)
    wizard.show()
    wizard.next()
    qtbot.wait(10)
    wizard.native_page.select_language("en")
    wizard.next()
    qtbot.wait(10)
    wizard.llm_mode_page.select_embedded()
    wizard.next()
    qtbot.wait(10)
    wizard.llm_page.set_huggingface_token("hf_test_token")
    wizard.next()
    qtbot.wait(10)

    assert wizard.settings.huggingface_token == "hf_test_token"


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
