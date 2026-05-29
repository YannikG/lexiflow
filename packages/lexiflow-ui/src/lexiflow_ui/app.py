"""Application entry: QApplication and main window."""

from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from lexiflow_ui.main_window import MainWindow


def run(argv: list[str] | None = None) -> int:
    app = QApplication.instance()
    if app is None:
        if argv is None:
            argv = sys.argv
        app = QApplication(argv)

    window = MainWindow()
    window.show()
    return app.exec()
