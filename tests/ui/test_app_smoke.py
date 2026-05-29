from lexiflow_ui.app import run
from PySide6.QtWidgets import QApplication


def test_run_returns_zero_when_app_quits(qtbot, monkeypatch) -> None:
    monkeypatch.setattr(QApplication, "exec", lambda self: 0)
    assert run() == 0


def test_main_window_has_lexiflow_title(qtbot) -> None:
    from lexiflow_ui.main_window import MainWindow

    window = MainWindow()
    qtbot.addWidget(window)
    assert window.windowTitle() == "LexiFlow"
