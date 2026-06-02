"""Confirm application quit when background jobs are active."""

from __future__ import annotations

from lexiflow_core.jobs.models import JobStatus
from lexiflow_core.jobs.service import JobService
from PySide6.QtWidgets import QMessageBox, QWidget

from lexiflow_ui.llama_server_supervisor import LlamaServerSupervisor
from lexiflow_ui.worker_supervisor import WorkerSupervisor


def confirm_application_quit(
    parent: QWidget,
    *,
    job_service: JobService,
    worker_supervisor: WorkerSupervisor,
    llama_supervisor: LlamaServerSupervisor | None,
) -> bool:
    """Return True when the app may exit. Shut down supervisors when allowed."""
    jobs = job_service.list_jobs()
    running = sum(1 for job in jobs if job.status == JobStatus.RUNNING)
    pending = sum(1 for job in jobs if job.status == JobStatus.PENDING)
    if running == 0 and pending == 0:
        _shutdown_supervisors(
            worker_supervisor=worker_supervisor,
            llama_supervisor=llama_supervisor,
            wait=True,
        )
        return True

    running_label = "job" if running == 1 else "jobs"
    pending_label = "job" if pending == 1 else "jobs"
    message = (
        f"{running} running {running_label} and {pending} pending {pending_label} "
        "are still in the queue.\n\n"
        "Wait for the current work to finish, or quit anyway and resume pending "
        "jobs on the next launch."
    )
    wait_button = QMessageBox.StandardButton.Yes
    quit_button = QMessageBox.StandardButton.No
    box = QMessageBox(parent)
    box.setWindowTitle("Quit LexiFlow")
    box.setText(message)
    box.setStandardButtons(wait_button | quit_button)
    box.button(wait_button).setText("Wait")
    box.button(quit_button).setText("Quit anyway")
    box.setDefaultButton(wait_button)
    choice = box.exec()

    if choice == int(wait_button):
        return False
    if choice == int(quit_button):
        job_service.recover_on_startup()
        _shutdown_supervisors(
            worker_supervisor=worker_supervisor,
            llama_supervisor=llama_supervisor,
            wait=False,
        )
        return True
    return False


def _shutdown_supervisors(
    *,
    worker_supervisor: WorkerSupervisor,
    llama_supervisor: LlamaServerSupervisor | None,
    wait: bool,
) -> None:
    if llama_supervisor is not None:
        llama_supervisor.shutdown(wait=wait)
    worker_supervisor.shutdown(wait=wait)
