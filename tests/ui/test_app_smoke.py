from lexiflow_core.config.settings import Settings
from lexiflow_core.config.settings_store import SettingsStore
from lexiflow_ui.app import run
from lexiflow_ui.main_window import MainWindow
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication


class _SmokeInstanceGuard:
    def try_acquire(self) -> bool:
        return True

    def handle_secondary_launch(self) -> int:
        return 0

    def listen_for_activation(self, _callback: object) -> None:
        return None

    def release(self) -> None:
        return None


def test_app_smoke(qtbot, monkeypatch, tmp_path) -> None:
    config_dir = tmp_path / "config"
    data_root = tmp_path / "library"
    store = SettingsStore(config_dir=config_dir)
    store.save(Settings(data_root=data_root, onboarding_complete=True))
    original_show = MainWindow.show

    def show_then_close(self: MainWindow) -> None:
        original_show(self)
        qtbot.addWidget(self)
        assert self.windowTitle() == "LexiFlow"
        QTimer.singleShot(0, self.close)

    def exec_process_events(_self: QApplication) -> int:
        _self.processEvents()
        return 0

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
