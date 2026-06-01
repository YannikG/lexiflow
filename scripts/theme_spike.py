"""Manual theme spike for phase 9-2 — run on macOS, save screenshots."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from lexiflow_ui.theme import apply_app_theme
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


def _build_demo_window(title: str) -> QMainWindow:
    window = QMainWindow()
    window.setWindowTitle(title)
    central = QWidget()
    layout = QVBoxLayout(central)
    layout.addWidget(QLabel("LexiFlow theme spike"))
    layout.addWidget(QLineEdit(placeholderText="Search…"))
    row = QHBoxLayout()
    row.addWidget(QPushButton("Primary"))
    row.addWidget(QPushButton("Secondary"))
    layout.addLayout(row)
    window.setCentralWidget(central)
    window.resize(480, 240)
    return window


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 9-2 theme spike")
    parser.add_argument(
        "variant",
        choices=["fusion", "dark_theme", "light_theme"],
    )
    parser.add_argument(
        "--screenshot",
        type=Path,
        default=None,
        help="PNG output path (auto-closes after capture)",
    )
    args = parser.parse_args()

    app = QApplication(sys.argv)
    title = f"LexiFlow spike — {args.variant}"
    window = _build_demo_window(title)

    if args.variant == "fusion":
        app.setStyle("Fusion")
    elif args.variant == "dark_theme":
        apply_app_theme(app, theme="dark")
    elif args.variant == "light_theme":
        apply_app_theme(app, theme="light")

    window.show()

    if args.screenshot is not None:
        args.screenshot.parent.mkdir(parents=True, exist_ok=True)

        def capture() -> None:
            window.grab().save(str(args.screenshot))
            app.quit()

        QTimer.singleShot(300, capture)
        return app.exec()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
