"""Run blocking work off the Qt GUI thread with a modal progress dialog."""

from __future__ import annotations

import queue
import threading
from collections.abc import Callable

from PySide6.QtCore import QEventLoop, QObject, Qt, QTimer, Signal
from PySide6.QtWidgets import QApplication, QProgressDialog, QWidget

_DEFAULT_TIMEOUT_SECONDS = 7200.0

_ProgressCallback = Callable[[float], None]
_StatusCallback = Callable[[str], None]
_WorkCallback = Callable[[_ProgressCallback, _StatusCallback], None]

_Update = tuple[str, float | str | None]


def _format_background_error(exc: BaseException) -> str:
    if isinstance(exc, KeyboardInterrupt):
        return "Operation cancelled."
    if isinstance(exc, SystemExit):
        code = exc.code
        if isinstance(code, int) and code != 0:
            return f"Operation exited with code {code}."
        if isinstance(code, str) and code:
            return code
        return "Operation exited unexpectedly."
    return str(exc)


class _ProgressRelay(QObject):
    """Emit progress updates on the GUI thread from a worker queue."""

    progress = Signal(float)
    status = Signal(str)


def run_with_progress_dialog(
    parent: QWidget,
    *,
    title: str,
    initial_status: str,
    work: _WorkCallback,
    timeout_seconds: float = _DEFAULT_TIMEOUT_SECONDS,
) -> tuple[bool, str | None]:
    """Run work on a background thread; keep the UI responsive.

    Blocking work runs on a ``threading.Thread`` because ``QThread`` triggers
    native crashes under ``pytest-qt`` on macOS in CI. Updates are relayed to
    the GUI thread through Qt signals; a watchdog timer bounds ``QEventLoop``
    wait time even when the worker blocks indefinitely.
    """
    progress = QProgressDialog(title, None, 0, 100, parent)
    progress.setWindowModality(Qt.WindowModality.WindowModal)
    progress.setMinimumDuration(0)
    progress.setCancelButton(None)
    progress.setAutoClose(False)
    progress.setAutoReset(False)
    progress.setMinimumWidth(480)
    progress.setLabelText(initial_status)
    progress.setValue(0)
    progress.show()
    QApplication.processEvents()

    relay = _ProgressRelay()
    updates: queue.Queue[_Update] = queue.Queue()
    finished_event = threading.Event()
    error_message: str | None = None
    worker_finished = False
    loop = QEventLoop()

    relay.progress.connect(
        lambda value: progress.setValue(min(100, max(0, int(value * 100))))
    )
    relay.status.connect(progress.setLabelText)

    def drain_updates() -> None:
        nonlocal error_message
        while True:
            try:
                kind, payload = updates.get_nowait()
            except queue.Empty:
                break
            if kind == "progress" and isinstance(payload, float):
                relay.progress.emit(payload)
            elif kind == "status" and isinstance(payload, str):
                relay.status.emit(payload)
            elif kind == "error" and isinstance(payload, str):
                error_message = payload

    def finish_loop(message: str | None = None) -> None:
        nonlocal error_message, worker_finished
        worker_finished = True
        if message is not None:
            error_message = message
        loop.quit()

    def on_watchdog() -> None:
        if not worker_finished:
            finish_loop("Operation timed out.")

    def poll_worker() -> None:
        drain_updates()
        if finished_event.is_set():
            poll_timer.stop()
            finish_loop()

    def progress_from_worker(value: float) -> None:
        updates.put(("progress", value))

    def status_from_worker(message: str) -> None:
        updates.put(("status", message))

    def run_work() -> None:
        try:
            work(progress_from_worker, status_from_worker)
        except BaseException as exc:
            updates.put(("error", _format_background_error(exc)))
        finally:
            finished_event.set()

    worker = threading.Thread(target=run_work, daemon=True)
    worker.start()

    poll_timer = QTimer()
    poll_timer.setInterval(16)
    poll_timer.timeout.connect(poll_worker)

    watchdog = QTimer()
    watchdog.setSingleShot(True)
    watchdog.timeout.connect(on_watchdog)
    watchdog.start(max(1, int(timeout_seconds * 1000)))

    poll_timer.start()
    loop.exec()
    poll_timer.stop()
    watchdog.stop()
    drain_updates()
    worker.join(timeout=5.0)

    progress.close()

    if not worker_finished:
        return False, error_message or "Operation timed out."
    if error_message is not None:
        return False, error_message
    return True, None
