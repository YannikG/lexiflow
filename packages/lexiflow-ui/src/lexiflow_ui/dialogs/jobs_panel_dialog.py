"""Panel listing background jobs with retry and cancel controls."""

from __future__ import annotations

from pathlib import Path
from uuid import UUID

from lexiflow_core.jobs.models import JobRecord, JobStatus
from lexiflow_core.jobs.service import JobService
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from lexiflow_ui.dialogs.job_detail_dialog import open_job_detail
from lexiflow_ui.jobs_display import JOB_TABLE_HEADERS, job_table_cell_texts

_TAB_QUEUE = 0
_TAB_SUCCESS = 1
_TAB_FAILED = 2

_POLL_INTERVAL_MS = 1000


def open_jobs_panel(parent: QWidget, *, data_root: Path) -> None:
    dialog = JobsPanelDialog(data_root=data_root, parent=parent)
    dialog.exec()


class JobsPanelDialog(QDialog):
    def __init__(
        self,
        *,
        data_root: Path,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("jobs_panel_dialog")
        self.setWindowTitle("Background jobs")
        self.resize(720, 360)
        self._data_root = data_root
        self._job_service = JobService(data_root)
        self._selected_id: UUID | None = None

        layout = QVBoxLayout(self)

        self._tabs = QTabWidget(self)
        self._tabs.setObjectName("jobs_panel_tabs")
        self._tabs.addTab(QWidget(), "Running / pending")
        self._tabs.addTab(QWidget(), "Success")
        self._tabs.addTab(QWidget(), "Failed")
        layout.addWidget(self._tabs)

        self._table = QTableWidget(self)
        self._table.setObjectName("jobs_panel_table")
        self._table.setColumnCount(len(JOB_TABLE_HEADERS))
        self._table.setHorizontalHeaderLabels(list(JOB_TABLE_HEADERS))
        header = self._table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        for column in (2, 3, 4, 5):
            header.setSectionResizeMode(column, QHeaderView.ResizeMode.ResizeToContents)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.verticalHeader().setVisible(False)
        self._table.itemSelectionChanged.connect(self._on_selection_changed)
        self._table.cellDoubleClicked.connect(self._on_cell_double_clicked)
        layout.addWidget(self._table)

        button_row = QHBoxLayout()
        button_row.addStretch(1)
        self._retry_button = QPushButton("Retry", self)
        self._retry_button.setObjectName("jobs_panel_retry_button")
        self._retry_button.clicked.connect(self._retry_selected)
        self._cancel_button = QPushButton("Cancel", self)
        self._cancel_button.setObjectName("jobs_panel_cancel_button")
        self._cancel_button.clicked.connect(self._cancel_selected)
        self._close_button = QPushButton("Close", self)
        self._close_button.setObjectName("jobs_panel_close_button")
        self._close_button.clicked.connect(self.reject)
        button_row.addWidget(self._retry_button)
        button_row.addWidget(self._cancel_button)
        button_row.addWidget(self._close_button)
        layout.addLayout(button_row)

        self._tabs.currentChanged.connect(self._on_tab_changed)

        self._poll_timer = QTimer(self)
        self._poll_timer.setInterval(_POLL_INTERVAL_MS)
        self._poll_timer.timeout.connect(self._poll_jobs)

        self._refresh_table()
        self._poll_timer.start()

    def closeEvent(self, event: QCloseEvent) -> None:
        self._poll_timer.stop()
        super().closeEvent(event)

    def _poll_jobs(self) -> None:
        self._refresh_table()

    def _jobs_for_tab(self, tab_index: int) -> list[JobRecord]:
        if tab_index == _TAB_QUEUE:
            return self._job_service.list_queue_jobs(limit=50)
        if tab_index == _TAB_SUCCESS:
            return self._job_service.list_completed_jobs()
        return self._job_service.list_failed_jobs(limit=20)

    def _on_tab_changed(self, _index: int) -> None:
        self._selected_id = None
        self._refresh_table()

    def _refresh_table(self) -> None:
        jobs = self._jobs_for_tab(self._tabs.currentIndex())
        selected_row = -1
        if self._selected_id is not None:
            for row, job in enumerate(jobs):
                if job.id == self._selected_id:
                    selected_row = row
                    break
        self._table.blockSignals(True)
        try:
            self._table.setRowCount(len(jobs))
            for row, job in enumerate(jobs):
                for column, text in enumerate(job_table_cell_texts(job)):
                    item = self._table.item(row, column)
                    if item is None:
                        item = QTableWidgetItem(text)
                        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                        if column == 0:
                            item.setData(Qt.ItemDataRole.UserRole, str(job.id))
                        self._table.setItem(row, column, item)
                    else:
                        item.setText(text)
                        if column == 0:
                            item.setData(Qt.ItemDataRole.UserRole, str(job.id))
            if selected_row >= 0:
                self._table.selectRow(selected_row)
        finally:
            self._table.blockSignals(False)
        self._on_selection_changed()

    def _job_for_row(self, row: int) -> JobRecord | None:
        if row < 0:
            return None
        item = self._table.item(row, 0)
        if item is None:
            return None
        raw_id = item.data(Qt.ItemDataRole.UserRole)
        try:
            job_id = UUID(str(raw_id))
        except ValueError:
            return None
        return self._job_service.get(job_id)

    def _on_selection_changed(self) -> None:
        job = self._job_for_row(self._table.currentRow())
        if job is None:
            self._selected_id = None
            self._retry_button.setEnabled(False)
            self._cancel_button.setEnabled(False)
            return
        self._selected_id = job.id
        self._retry_button.setEnabled(
            self._tabs.currentIndex() == _TAB_FAILED and job.status == JobStatus.FAILED
        )
        self._cancel_button.setEnabled(
            self._tabs.currentIndex() == _TAB_QUEUE
            and job.status in (JobStatus.PENDING, JobStatus.RUNNING)
        )

    def _on_cell_double_clicked(self, row: int, _column: int) -> None:
        job = self._job_for_row(row)
        if job is None:
            return
        open_job_detail(self, job)

    def _retry_selected(self) -> None:
        if self._selected_id is None:
            return
        self._job_service.retry(self._selected_id)
        self._tabs.setCurrentIndex(_TAB_QUEUE)
        self._refresh_table()

    def _cancel_selected(self) -> None:
        if self._selected_id is None:
            return
        self._job_service.cancel(self._selected_id)
        self._refresh_table()
