"""Primary application window."""

from PySide6.QtWidgets import QMainWindow, QWidget


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("LexiFlow")
        self.setCentralWidget(QWidget())
