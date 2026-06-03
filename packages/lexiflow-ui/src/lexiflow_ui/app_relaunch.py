"""Relaunch LexiFlow in a new process."""

from __future__ import annotations

import sys

from PySide6.QtCore import QProcess
from PySide6.QtWidgets import QApplication, QMessageBox, QWidget


def prompt_restart_lexiflow(parent: QWidget, *, reason: str) -> bool:
    """Ask whether to restart now. Return True when the user chose restart."""
    answer = QMessageBox.question(
        parent,
        "Restart required",
        f"{reason}\n\nRestart LexiFlow now to apply the change?",
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        QMessageBox.StandardButton.Yes,
    )
    return answer == QMessageBox.StandardButton.Yes


def relaunch_application() -> None:
    """Start a fresh process and quit the current one."""
    app = QApplication.instance()
    if app is None:
        return
    executable = app.arguments()[0] if app.arguments() else sys.argv[0]
    arguments = app.arguments()[1:] if len(app.arguments()) > 1 else sys.argv[1:]
    QProcess.startDetached(executable, arguments)
    app.quit()
