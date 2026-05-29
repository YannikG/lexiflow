"""Single-instance guard tests."""

from __future__ import annotations

import pytest
from lexiflow_ui.single_instance import (
    SecondInstanceChoice,
    SingleInstanceGuard,
)


@pytest.fixture
def unique_server_name() -> str:
    import uuid

    return f"lexiflow-test-{uuid.uuid4().hex}"


def test_first_launch_acquires_server(qtbot, unique_server_name: str) -> None:
    guard = SingleInstanceGuard(server_name=unique_server_name)
    assert guard.try_acquire() is True
    assert guard.server_name == unique_server_name


def test_second_launch_fails_acquire(qtbot, unique_server_name: str) -> None:
    primary = SingleInstanceGuard(server_name=unique_server_name)
    assert primary.try_acquire() is True

    secondary = SingleInstanceGuard(server_name=unique_server_name)
    assert secondary.try_acquire() is False

    primary.release()


def test_second_instance_dialog_records_choice(qtbot, unique_server_name: str) -> None:
    choices: list[SecondInstanceChoice] = []

    def dialog_factory() -> SecondInstanceChoice:
        return SecondInstanceChoice.OPEN_EXISTING

    primary = SingleInstanceGuard(server_name=unique_server_name)
    assert primary.try_acquire() is True

    secondary = SingleInstanceGuard(
        server_name=unique_server_name,
        second_instance_dialog=dialog_factory,
        on_second_instance_choice=choices.append,
    )
    assert secondary.try_acquire() is False
    exit_code = secondary.handle_secondary_launch()
    assert exit_code == 0
    assert choices == [SecondInstanceChoice.OPEN_EXISTING]

    primary.release()


def test_second_instance_close_choice_is_recorded(
    qtbot, unique_server_name: str
) -> None:
    choices: list[SecondInstanceChoice] = []

    def dialog_factory() -> SecondInstanceChoice:
        return SecondInstanceChoice.CLOSE

    primary = SingleInstanceGuard(server_name=unique_server_name)
    assert primary.try_acquire() is True

    secondary = SingleInstanceGuard(
        server_name=unique_server_name,
        second_instance_dialog=dialog_factory,
        on_second_instance_choice=choices.append,
    )
    assert secondary.try_acquire() is False
    assert secondary.handle_secondary_launch() == 0
    assert choices == [SecondInstanceChoice.CLOSE]

    primary.release()


def test_try_acquire_recovers_stale_server_name(
    qtbot, unique_server_name: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    from PySide6.QtNetwork import QLocalServer

    listen_attempts: list[str] = []
    original_listen = QLocalServer.listen

    def patched_listen(server: QLocalServer, name: str) -> bool:
        listen_attempts.append(name)
        if len(listen_attempts) == 1:
            return False
        return original_listen(server, name)

    monkeypatch.setattr(QLocalServer, "listen", patched_listen)

    guard = SingleInstanceGuard(server_name=unique_server_name)
    assert guard.try_acquire() is True
    assert len(listen_attempts) == 2

    guard.release()


def test_primary_receives_activation_message(qtbot, unique_server_name: str) -> None:
    from lexiflow_ui.single_instance import ACTIVATE_MESSAGE
    from PySide6.QtNetwork import QLocalSocket
    from PySide6.QtWidgets import QApplication

    primary = SingleInstanceGuard(server_name=unique_server_name)
    assert primary.try_acquire() is True

    activated: list[bool] = []

    def on_activate() -> None:
        activated.append(True)

    primary.listen_for_activation(on_activate)

    client = QLocalSocket()
    client.connectToServer(unique_server_name)
    assert client.waitForConnected(1000)
    client.write(ACTIVATE_MESSAGE)
    client.flush()
    client.waitForBytesWritten(1000)
    client.disconnectFromServer()

    app = QApplication.instance()
    assert app is not None
    for _ in range(100):
        app.processEvents()
        if activated:
            break
        qtbot.wait(20)

    assert activated == [True]

    primary.release()


def test_default_server_name_uses_username(qtbot) -> None:
    import getpass

    guard = SingleInstanceGuard()
    assert guard.server_name == f"lexiflow-{getpass.getuser()}"
