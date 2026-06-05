"""Run blocking work off the Qt GUI thread with a modal progress dialog."""

from __future__ import annotations

import queue
import threading
from collections.abc import Callable

from PySide6.QtCore import QEventLoop, Qt, QTimer
from PySide6.QtWidgets import QApplication, QProgressDialog, QWidget

_ProgressCallback = Callable[[float], None]
_StatusCallback = Callable[[str], None]
_WorkCallback = Callable[[_ProgressCallback, _StatusCallback], None]

_Update = tuple[str, float | str | None]


def run_with_progress_dialog(
    parent: QWidget,
    *,
    title: str,
    initial_status: str,
    work: _WorkCallback,
) -> tuple[bool, str | None]:
    """Run work on a background thread; keep the UI responsive."""
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

    updates: queue.Queue[_Update] = queue.Queue()
    finished = threading.Event()
    error_message: list[str | None] = [None]

    def on_progress(value: float) -> None:
        progress.setValue(min(100, max(0, int(value * 100))))

    def on_status(message: str) -> None:
        progress.setLabelText(message)

    def progress_from_worker(value: float) -> None:
        updates.put(("progress", value))

    def status_from_worker(message: str) -> None:
        updates.put(("status", message))

    def drain_updates() -> None:
        while True:
            try:
                kind, payload = updates.get_nowait()
            except queue.Empty:
                break
            if kind == "progress" and isinstance(payload, float):
                on_progress(payload)
            elif kind == "status" and isinstance(payload, str):
                on_status(payload)
            elif kind == "error" and isinstance(payload, str):
                error_message[0] = payload

    def run_work() -> None:
        try:
            work(progress_from_worker, status_from_worker)
        except Exception as exc:
            updates.put(("error", str(exc)))
        finally:
            finished.set()

    worker = threading.Thread(target=run_work, daemon=True)
    worker.start()

    loop = QEventLoop()
    timer = QTimer()
    timer.setInterval(16)

    def poll_worker() -> None:
        drain_updates()
        if finished.is_set():
            timer.stop()
            loop.quit()

    timer.timeout.connect(poll_worker)
    timer.start()
    loop.exec()
    timer.stop()

    drain_updates()
    worker.join(timeout=30.0)
    progress.close()

    if worker.is_alive():
        return False, "Download timed out."
    if error_message[0] is not None:
        return False, error_message[0]
    return True, None
