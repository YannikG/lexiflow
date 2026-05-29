"""Ensure only one LexiFlow UI instance runs per user session."""

from __future__ import annotations

import getpass
from collections.abc import Callable
from enum import Enum

from PySide6.QtCore import QObject
from PySide6.QtNetwork import QLocalServer, QLocalSocket
from PySide6.QtWidgets import QMessageBox

ACTIVATE_MESSAGE = b"activate"


class SecondInstanceChoice(Enum):
    OPEN_EXISTING = "open_existing"
    CLOSE = "close"


def default_server_name() -> str:
    return f"lexiflow-{getpass.getuser()}"


class SingleInstanceGuard(QObject):
    def __init__(
        self,
        *,
        server_name: str | None = None,
        second_instance_dialog: Callable[[], SecondInstanceChoice] | None = None,
        on_second_instance_choice: Callable[[SecondInstanceChoice], None] | None = None,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._server_name = (
            server_name if server_name is not None else default_server_name()
        )
        self._server = QLocalServer(self)
        self._is_primary = False
        self._second_instance_dialog = (
            second_instance_dialog or self._show_second_instance_dialog
        )
        self._on_second_instance_choice = on_second_instance_choice

    @property
    def server_name(self) -> str:
        return self._server_name

    def try_acquire(self) -> bool:
        if self._is_primary and self._server.isListening():
            return True

        probe = QLocalSocket()
        probe.connectToServer(self._server_name)
        if probe.waitForConnected(200):
            probe.disconnectFromServer()
            return False

        if self._server.listen(self._server_name):
            self._is_primary = True
            return True

        QLocalServer.removeServer(self._server_name)
        if self._server.listen(self._server_name):
            self._is_primary = True
            return True

        return False

    def listen_for_activation(self, callback: Callable[[], None]) -> None:
        if self._server.isListening():
            self._server.newConnection.connect(
                lambda: self._handle_new_connection(callback)
            )

    def handle_secondary_launch(self) -> int:
        choice = self._second_instance_dialog()
        if self._on_second_instance_choice is not None:
            self._on_second_instance_choice(choice)
        if choice is SecondInstanceChoice.OPEN_EXISTING:
            socket = QLocalSocket()
            socket.connectToServer(self._server_name)
            if socket.waitForConnected(1000):
                socket.write(ACTIVATE_MESSAGE)
                socket.flush()
                socket.waitForBytesWritten(1000)
                socket.disconnectFromServer()
        return 0

    def release(self) -> None:
        if self._server.isListening():
            self._server.close()
        QLocalServer.removeServer(self._server_name)
        self._is_primary = False

    def _handle_new_connection(self, callback: Callable[[], None]) -> None:
        while self._server.hasPendingConnections():
            socket = self._server.nextPendingConnection()
            if socket is None:
                continue
            if socket.bytesAvailable() == 0:
                socket.waitForReadyRead(500)
            if bytes(socket.readAll()) == ACTIVATE_MESSAGE:
                callback()
            socket.disconnectFromServer()
            socket.deleteLater()

    def _show_second_instance_dialog(self) -> SecondInstanceChoice:
        box = QMessageBox()
        box.setWindowTitle("LexiFlow is already running")
        box.setText("Another LexiFlow window is already open.")
        open_button = box.addButton("Open existing", QMessageBox.ButtonRole.AcceptRole)
        box.addButton("Close", QMessageBox.ButtonRole.RejectRole)
        box.exec()
        if box.clickedButton() is open_button:
            return SecondInstanceChoice.OPEN_EXISTING
        return SecondInstanceChoice.CLOSE
