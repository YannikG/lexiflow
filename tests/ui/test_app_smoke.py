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


def test_app_smoke(qtbot, monkeypatch) -> None:
    original_show = MainWindow.show

    def show_then_quit(self: MainWindow) -> None:
        original_show(self)
        qtbot.addWidget(self)
        assert self.windowTitle() == "LexiFlow"
        QTimer.singleShot(0, self.close)
        app = QApplication.instance()
        assert app is not None
        QTimer.singleShot(0, app.quit)

    monkeypatch.setattr(MainWindow, "show", show_then_quit)
    assert run(argv=["lexiflow-test"], instance_guard=_SmokeInstanceGuard()) == 0
