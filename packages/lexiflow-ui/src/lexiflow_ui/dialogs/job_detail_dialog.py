"""Dialog showing full details for a single background job."""

from __future__ import annotations

from lexiflow_core.jobs.models import JobRecord
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from lexiflow_ui.jobs_display import format_job_full_detail


def open_job_detail(parent: QWidget | None, job: JobRecord) -> None:
    dialog = JobDetailDialog(job=job, parent=parent)
    dialog.exec()


class JobDetailDialog(QDialog):
    def __init__(
        self,
        *,
        job: JobRecord,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("job_detail_dialog")
        self.setWindowTitle(f"Job — {job.job_type.value}")
        self.resize(520, 420)

        layout = QVBoxLayout(self)
        body = QPlainTextEdit(self)
        body.setObjectName("job_detail_body")
        body.setReadOnly(True)
        body.setPlainText(format_job_full_detail(job))
        layout.addWidget(body)

        button_row = QHBoxLayout()
        button_row.addStretch(1)
        close_button = QPushButton("Close", self)
        close_button.setObjectName("job_detail_close_button")
        close_button.clicked.connect(self.accept)
        button_row.addWidget(close_button)
        layout.addLayout(button_row)
