"""Qt helpers for jobs panel UI tests (public widget lookup only)."""

from __future__ import annotations

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QDialog,
    QPushButton,
    QTabBar,
    QTableWidget,
)


def jobs_panel_table(dialog: QDialog) -> QTableWidget:
    table = dialog.findChild(QTableWidget, "jobs_panel_table")
    assert table is not None
    return table


def jobs_panel_tabs(dialog: QDialog) -> QTabBar:
    tabs = dialog.findChild(QTabBar, "jobs_panel_tabs")
    assert tabs is not None
    return tabs


def jobs_panel_retry_button(dialog: QDialog) -> QPushButton:
    button = dialog.findChild(QPushButton, "jobs_panel_retry_button")
    assert button is not None
    return button


def jobs_panel_cancel_button(dialog: QDialog) -> QPushButton:
    button = dialog.findChild(QPushButton, "jobs_panel_cancel_button")
    assert button is not None
    return button


def jobs_panel_poll_timer(dialog: QDialog) -> QTimer:
    timer = dialog.findChild(QTimer, "jobs_panel_poll_timer")
    assert timer is not None
    return timer
