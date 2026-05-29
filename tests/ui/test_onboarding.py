"""Onboarding wizard and app gate tests."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from lexiflow_core.config.settings import Settings
from lexiflow_core.config.settings_store import SettingsStore
from lexiflow_core.models.download import (
    FakeModelDownloader,
    ModelAccessError,
    NetworkError,
)
from lexiflow_core.models.lockfile import load_models_lock
from lexiflow_core.models.model_hints import gemma_hub_page_url
from lexiflow_core.models.requirements import EMBEDDED_GEMMA_ID, EMBEDDING_MINILM_ID
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
    ) -> None:
        from lexiflow_core.models.lockfile import ModelArtifact

        assert isinstance(artifact, ModelArtifact)
        del token, on_progress
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
    if not use_ollama:
        qtbot.waitUntil(
            lambda: wizard.bootstrap_page.bootstrap_complete,
            timeout=10000,
        )
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
    assert downloader.call_count >= 1
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


def test_ollama_scenario_skips_download_models_page(qtbot, tmp_path: Path) -> None:
    """Ollama path must not show the Download models wizard page or fetch Gemma."""
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
    assert wizard.currentPage() is not wizard.bootstrap_page
    assert wizard.bootstrap_page.title() == "Download models"
    assert not wizard.bootstrap_page.bootstrap_complete
    assert downloader.artifact_ids == [EMBEDDING_MINILM_ID]
    assert EMBEDDED_GEMMA_ID not in downloader.artifact_ids

    wizard.target_page.select_language("es")
    wizard.target_page.select_level("A2")
    finish = wizard.button(QWizard.WizardButton.FinishButton)
    qtbot.mouseClick(finish, Qt.MouseButton.LeftButton)
    qtbot.wait(10)

    loaded = store.load()
    assert loaded.onboarding_complete is True
    assert loaded.ollama_url == "http://127.0.0.1:11434"


def test_ollama_embedding_download_failure_shows_clear_message_and_retry(
    qtbot, tmp_path: Path
) -> None:
    config_dir = tmp_path / "config"
    data_root = tmp_path / "library"
    store = SettingsStore(config_dir=config_dir)
    settings = Settings(data_root=data_root, onboarding_complete=False)
    failing = FakeModelDownloader(error=NetworkError("offline"), fail_on_call=1)
    wizard = OnboardingWizard(
        data_root=data_root,
        settings_store=store,
        settings=settings,
        system_info=FakeSystemInfo(16 * 1024**3),
        model_store=_make_model_store(data_root, downloader=failing),
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

    wizard.next()
    qtbot.wait(50)

    error_text = wizard.llm_page.download_status_text().lower()
    assert "embedding model" in error_text
    assert "ollama is connected" in error_text
    assert wizard.llm_page.download_retry_button().isVisible()

    succeeding = FakeModelDownloader()
    wizard.bootstrap_page.set_model_store(
        _make_model_store(data_root, downloader=succeeding)
    )
    qtbot.mouseClick(wizard.llm_page.download_retry_button(), Qt.MouseButton.LeftButton)
    qtbot.wait(50)

    assert not wizard.llm_page.is_download_status_visible()
    assert wizard.currentId() == 3


def test_switching_llm_mode_clears_stale_download_error(qtbot, tmp_path: Path) -> None:
    config_dir = tmp_path / "config"
    data_root = tmp_path / "library"
    store = SettingsStore(config_dir=config_dir)
    failing = FakeModelDownloader(error=NetworkError("offline"), fail_on_call=1)
    wizard = OnboardingWizard(
        data_root=data_root,
        settings_store=store,
        settings=Settings(data_root=data_root, onboarding_complete=False),
        system_info=FakeSystemInfo(16 * 1024**3),
        model_store=_make_model_store(data_root, downloader=failing),
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
    wizard.next()
    qtbot.wait(50)
    assert wizard.llm_page.is_download_status_visible()

    back = wizard.button(QWizard.WizardButton.BackButton)
    qtbot.mouseClick(back, Qt.MouseButton.LeftButton)
    qtbot.wait(10)
    wizard.llm_mode_page.select_embedded()
    wizard.next()
    qtbot.wait(10)
    assert not wizard.llm_page.is_download_status_visible()
    assert not wizard.llm_page.download_retry_button().isVisible()


def test_embedded_scenario_shows_download_models_page(qtbot, tmp_path: Path) -> None:
    """Embedded path uses the Download models page before target language."""
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
    assert wizard.llm_page.nextId() == 4

    wizard.next()
    qtbot.waitUntil(
        lambda: wizard.currentPage() is wizard.bootstrap_page,
        timeout=10000,
    )
    qtbot.waitUntil(
        lambda: wizard.bootstrap_page.bootstrap_complete,
        timeout=10000,
    )

    assert wizard.bootstrap_page.bootstrap_complete is True
    assert EMBEDDING_MINILM_ID in downloader.artifact_ids
    assert EMBEDDED_GEMMA_ID in downloader.artifact_ids


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
    assert downloader.call_count == 1
    assert downloader.last_artifact is not None
    assert downloader.last_artifact.id == "embedding-minilm"


def test_ollama_path_skips_gemma_download(qtbot, tmp_path: Path) -> None:
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

    assert downloader.call_count == 1
    assert downloader.last_artifact is not None
    assert downloader.last_artifact.id == "embedding-minilm"
    assert store.load().ollama_url == "http://127.0.0.1:11434"


def test_hf_download_page_shows_gemma_license_guidance(qtbot, tmp_path: Path) -> None:
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

    steps_text = wizard.llm_page.gemma_license_steps_text()
    assert "accept the license" in steps_text.lower()
    assert gemma_hub_page_url() in steps_text
    assert wizard.llm_page.open_gemma_hub_button().isVisible()
    assert "Accept the Gemma license" in wizard.llm_page.subTitle()


def test_bootstrap_access_error_shows_gemma_help(qtbot, tmp_path: Path) -> None:
    config_dir = tmp_path / "config"
    data_root = tmp_path / "library"
    store = SettingsStore(config_dir=config_dir)
    settings = Settings(data_root=data_root, onboarding_complete=False)
    failing = FakeModelDownloader(error=ModelAccessError("gated"), fail_on_call=1)
    wizard = OnboardingWizard(
        data_root=data_root,
        settings_store=store,
        settings=settings,
        system_info=FakeSystemInfo(16 * 1024**3),
        model_store=_make_model_store(data_root, downloader=failing),
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
    wizard.next()
    qtbot.waitUntil(
        lambda: wizard.bootstrap_page.is_bootstrap_error_visible(),
        timeout=10000,
    )

    error_text = wizard.bootstrap_page.bootstrap_error_text()
    assert "gated" in error_text.lower() or "gemma" in error_text.lower()
    assert gemma_hub_page_url() in error_text
    assert wizard.bootstrap_page.open_gemma_button().isVisible()
    assert wizard.bootstrap_page.retry_button().isVisible()


def test_bootstrap_network_error_shows_retry(qtbot, tmp_path: Path) -> None:
    config_dir = tmp_path / "config"
    data_root = tmp_path / "library"
    store = SettingsStore(config_dir=config_dir)
    settings = Settings(data_root=data_root, onboarding_complete=False)
    failing = FakeModelDownloader(error=NetworkError("offline"), fail_on_call=1)
    wizard = OnboardingWizard(
        data_root=data_root,
        settings_store=store,
        settings=settings,
        system_info=FakeSystemInfo(16 * 1024**3),
        model_store=_make_model_store(data_root, downloader=failing),
    )
    qtbot.addWidget(wizard)
    wizard.show()
    wizard.next()
    qtbot.wait(10)
    wizard.native_page.select_language("en")
    wizard.next()
    qtbot.wait(10)
    wizard.next()
    qtbot.wait(10)
    wizard.next()
    qtbot.waitUntil(
        lambda: wizard.bootstrap_page.is_bootstrap_error_visible(),
        timeout=10000,
    )
    assert "network" in wizard.bootstrap_page.bootstrap_error_text().lower()

    succeeding = FakeModelDownloader()
    wizard.bootstrap_page.set_model_store(
        _make_model_store(data_root, downloader=succeeding)
    )
    qtbot.mouseClick(wizard.bootstrap_page.retry_button(), Qt.MouseButton.LeftButton)
    qtbot.waitUntil(
        lambda: wizard.bootstrap_page.bootstrap_complete,
        timeout=10000,
    )

    assert wizard.bootstrap_page.bootstrap_complete is True
    assert not wizard.bootstrap_page.is_bootstrap_error_visible()


def test_manual_import_skips_bootstrap_page(qtbot, tmp_path: Path) -> None:
    config_dir = tmp_path / "config"
    data_root = tmp_path / "library"
    store = SettingsStore(config_dir=config_dir)
    settings = Settings(data_root=data_root, onboarding_complete=False)
    downloader = RecordingFakeDownloader()
    embedding_src = tmp_path / "minilm-src"
    embedding_src.mkdir()
    (embedding_src / "config.json").write_text("{}", encoding="utf-8")
    gemma_src = tmp_path / "gemma-src"
    gemma_src.mkdir()
    (gemma_src / "model.safetensors").write_text("x", encoding="utf-8")

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
    wizard.llm_mode_page.select_manual_import()
    wizard.next()
    qtbot.wait(10)
    wizard.llm_page.select_manual_import(
        embedding_dir=embedding_src,
        gemma_dir=gemma_src,
    )
    assert wizard.llm_page.skips_bootstrap_page()
    assert wizard.llm_page.nextId() == 5

    wizard.next()
    qtbot.wait(50)

    assert wizard.currentPage() is wizard.target_page
    assert not downloader.artifact_ids
    model_store = wizard.bootstrap_page.model_store
    assert model_store.is_installed(EMBEDDING_MINILM_ID)
    assert model_store.is_installed(EMBEDDED_GEMMA_ID)


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
