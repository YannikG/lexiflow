"""UI theme bootstrap tests (phase 9-2)."""

from __future__ import annotations

from pathlib import Path

import pytest
from lexiflow_core.config.settings import Settings
from lexiflow_core.config.settings_store import SettingsStore
from lexiflow_ui.app import run
from lexiflow_ui.main_window import MainWindow
from lexiflow_ui.theme import apply_app_theme, resolve_effective_theme
from lexiflow_ui.worker_supervisor import WorkerSupervisor
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QApplication

# Shell modules listed in packages/lexiflow-ui/docs/concepts/ui-theme.md
_SHELL_MODULE_PATHS = (
    "main_window.py",
    "widgets/sidebar.py",
    "widgets/empty_state.py",
    "widgets/reader_widget.py",
    "dialogs/add_text_dialog.py",
    "widgets/worker_status.py",
    "widgets/active_target_language.py",
    "onboarding/wizard.py",
    "onboarding/model_bootstrap_page.py",
    "onboarding/llm_mode_page.py",
    "onboarding/llm_config_page.py",
)


def _baseline_stylesheet(app: QApplication) -> str:
    """Return stylesheet for unthemed Fusion baseline."""
    return app.styleSheet()


def test_dark_theme_stylesheet_differs_from_fusion_baseline() -> None:
    app = QApplication.instance()
    assert app is not None
    app.setStyleSheet("")
    baseline = _baseline_stylesheet(app)

    apply_app_theme(app, theme="dark")

    themed = app.styleSheet()
    assert themed != baseline
    assert len(themed) > 100


def test_system_theme_resolves_to_dark_when_os_dark(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app = QApplication.instance()
    assert app is not None

    class _FakeStyleHints:
        def colorScheme(self) -> Qt.ColorScheme:
            return Qt.ColorScheme.Dark

    monkeypatch.setattr(app, "styleHints", lambda: _FakeStyleHints())
    assert resolve_effective_theme("system") == "dark"


def test_system_theme_resolves_to_light_when_os_light(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app = QApplication.instance()
    assert app is not None

    class _FakeStyleHints:
        def colorScheme(self) -> Qt.ColorScheme:
            return Qt.ColorScheme.Light

    monkeypatch.setattr(app, "styleHints", lambda: _FakeStyleHints())
    assert resolve_effective_theme("system") == "light"


def test_main_window_visible_with_dark_theme(qtbot, tmp_path) -> None:
    app = QApplication.instance()
    assert app is not None
    apply_app_theme(app, theme="dark")

    supervisor = WorkerSupervisor(data_root=tmp_path)
    window = MainWindow(
        supervisor=supervisor,
        settings=Settings(active_target_language="es", native_language="en"),
    )
    qtbot.addWidget(window)
    window.show()
    qtbot.waitExposed(window)
    assert window.isVisible()


class _SmokeInstanceGuard:
    def try_acquire(self) -> bool:
        return True

    def handle_secondary_launch(self) -> int:
        return 0

    def listen_for_activation(self, _callback: object) -> None:
        return None

    def release(self) -> None:
        return None


def test_run_applies_theme_once_before_main_window(
    qtbot, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    config_dir = tmp_path / "config"
    data_root = tmp_path / "library"
    store = SettingsStore(config_dir=config_dir)
    store.save(Settings(data_root=data_root, onboarding_complete=True, theme="dark"))

    apply_calls: list[str] = []
    events: list[str] = []
    original_apply = apply_app_theme
    original_init = MainWindow.__init__

    def track_apply(app: QApplication, *, theme: str) -> None:
        apply_calls.append(theme)
        events.append("apply")
        original_apply(app, theme=theme)  # type: ignore[arg-type]

    def track_init(self: MainWindow, *args: object, **kwargs: object) -> None:
        events.append("main_window")
        original_init(self, *args, **kwargs)  # type: ignore[arg-type]

    original_show = MainWindow.show

    def show_then_close(self: MainWindow) -> None:
        original_show(self)
        qtbot.addWidget(self)
        QTimer.singleShot(0, self.close)

    def exec_process_events(_self: QApplication) -> int:
        _self.processEvents()
        return 0

    monkeypatch.setattr("lexiflow_ui.app.apply_app_theme", track_apply)
    monkeypatch.setattr(MainWindow, "__init__", track_init)
    monkeypatch.setattr(MainWindow, "show", show_then_close)
    monkeypatch.setattr(QApplication, "exec", exec_process_events)

    assert (
        run(
            argv=["lexiflow-test"],
            instance_guard=_SmokeInstanceGuard(),
            settings_store=store,
        )
        == 0
    )
    assert apply_calls == ["dark"]
    assert events.index("apply") < events.index("main_window")


@pytest.mark.parametrize("relative_path", _SHELL_MODULE_PATHS)
def test_shell_modules_have_no_inline_stylesheet(relative_path: str) -> None:
    repo_root = Path(__file__).resolve().parents[2]
    ui_src = repo_root / "packages" / "lexiflow-ui" / "src" / "lexiflow_ui"
    source = (ui_src / relative_path).read_text(encoding="utf-8")
    assert "setStyleSheet(" not in source
