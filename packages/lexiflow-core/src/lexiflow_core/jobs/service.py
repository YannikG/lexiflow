"""Public job queue API."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from lexiflow_core.db.connection import connect_sqlite
from lexiflow_core.jobs.models import JobId, JobRecord, JobRequest
from lexiflow_core.jobs.queue_setup import ensure_job_queue
from lexiflow_core.jobs.store import JobStore


class JobService:
    def __init__(self, data_root: Path) -> None:
        self._db_path = ensure_job_queue(data_root)

    @property
    def db_path(self) -> Path:
        return self._db_path

    @contextmanager
    def _store(self) -> Iterator[JobStore]:
        connection = connect_sqlite(self._db_path)
        try:
            yield JobStore(connection)
        finally:
            connection.close()

    def enqueue(self, job: JobRequest) -> JobId:
        with self._store() as store:
            record = store.insert_pending(job)
            return record.id

    def list_jobs(self, limit: int = 50) -> list[JobRecord]:
        with self._store() as store:
            return store.list_jobs(limit=limit)

    def cancel(self, job_id: JobId) -> None:
        with self._store() as store:
            store.cancel_pending(job_id)

    def retry(self, job_id: JobId) -> None:
        with self._store() as store:
            store.retry_failed(job_id)

    def recover_on_startup(self) -> None:
        with self._store() as store:
            store.recover_running_to_pending()

    def claim_next(self) -> JobRecord | None:
        with self._store() as store:
            return store.claim_next_pending()

    def complete(self, job_id: JobId, result: dict[str, object]) -> JobRecord:
        with self._store() as store:
            return store.mark_completed(job_id, result)

    def fail(self, job_id: JobId, error_message: str) -> JobRecord:
        with self._store() as store:
            return store.mark_failed(job_id, error_message)

    def has_pending(self) -> bool:
        with self._store() as store:
            return store.has_pending()
