"""SQLite persistence for the job queue."""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from lexiflow_core.jobs.models import JobId, JobRecord, JobRequest, JobStatus, JobType

_COMPLETED_RETENTION = 20
_ISO_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"


class JobNotFoundError(Exception):
    """Raised when a job id does not exist in the queue."""


class JobStateError(Exception):
    """Raised when a job transition is not allowed for its current status."""


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _format_dt(value: datetime) -> str:
    return value.strftime(_ISO_FORMAT)


def _parse_dt(value: str | None) -> datetime | None:
    if value is None:
        return None
    return datetime.strptime(value, _ISO_FORMAT).replace(tzinfo=UTC)


def _row_to_record(row: sqlite3.Row) -> JobRecord:
    return JobRecord(
        id=UUID(row["id"]),
        job_type=JobType(row["job_type"]),
        status=JobStatus(row["status"]),
        payload=json.loads(row["payload_json"]),
        result=json.loads(row["result_json"]) if row["result_json"] else None,
        error_message=row["error_message"],
        created_at=_parse_dt(row["created_at"]) or _utc_now(),
        updated_at=_parse_dt(row["updated_at"]) or _utc_now(),
        started_at=_parse_dt(row["started_at"]),
        completed_at=_parse_dt(row["completed_at"]),
    )


class JobStore:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection
        self._connection.row_factory = sqlite3.Row

    def insert_pending(self, request: JobRequest) -> JobRecord:
        job_id = uuid4()
        now = _utc_now()
        self._connection.execute(
            """
            INSERT INTO jobs (
                id, job_type, status, payload_json, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                str(job_id),
                request.job_type.value,
                JobStatus.PENDING.value,
                json.dumps(request.payload),
                _format_dt(now),
                _format_dt(now),
            ),
        )
        self._connection.commit()
        record = self.get(job_id)
        if record is None:
            raise RuntimeError("failed to read inserted job")
        return record

    def get(self, job_id: JobId) -> JobRecord | None:
        row = self._connection.execute(
            "SELECT * FROM jobs WHERE id = ?",
            (str(job_id),),
        ).fetchone()
        if row is None:
            return None
        return _row_to_record(row)

    def list_jobs(self, limit: int = 50) -> list[JobRecord]:
        rows = self._connection.execute(
            """
            SELECT * FROM jobs
            ORDER BY COALESCE(completed_at, started_at, updated_at, created_at) DESC,
                     created_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [_row_to_record(row) for row in rows]

    def claim_next_pending(self) -> JobRecord | None:
        self._connection.execute("BEGIN IMMEDIATE")
        try:
            running = self._connection.execute(
                "SELECT 1 FROM jobs WHERE status = ? LIMIT 1",
                (JobStatus.RUNNING.value,),
            ).fetchone()
            if running is not None:
                self._connection.commit()
                return None

            row = self._connection.execute(
                """
                SELECT id FROM jobs
                WHERE status = ?
                ORDER BY created_at ASC
                LIMIT 1
                """,
                (JobStatus.PENDING.value,),
            ).fetchone()
            if row is None:
                self._connection.commit()
                return None

            now = _utc_now()
            cursor = self._connection.execute(
                """
                UPDATE jobs
                SET status = ?, started_at = ?, updated_at = ?
                WHERE id = ? AND status = ?
                """,
                (
                    JobStatus.RUNNING.value,
                    _format_dt(now),
                    _format_dt(now),
                    row["id"],
                    JobStatus.PENDING.value,
                ),
            )
            if cursor.rowcount != 1:
                self._connection.commit()
                return None
            self._connection.commit()
        except sqlite3.Error:
            self._connection.rollback()
            raise

        return self.get(UUID(row["id"]))

    def mark_completed(self, job_id: JobId, result: dict[str, Any]) -> JobRecord:
        now = _utc_now()
        cursor = self._connection.execute(
            """
            UPDATE jobs
            SET status = ?, result_json = ?, error_message = NULL,
                updated_at = ?, completed_at = ?
            WHERE id = ? AND status = ?
            """,
            (
                JobStatus.COMPLETED.value,
                json.dumps(result),
                _format_dt(now),
                _format_dt(now),
                str(job_id),
                JobStatus.RUNNING.value,
            ),
        )
        if cursor.rowcount != 1:
            raise JobStateError(f"job {job_id} is not running")
        self._connection.commit()
        self.prune_completed()
        record = self.get(job_id)
        if record is None:
            raise JobNotFoundError(str(job_id))
        return record

    def mark_failed(self, job_id: JobId, error_message: str) -> JobRecord:
        now = _utc_now()
        cursor = self._connection.execute(
            """
            UPDATE jobs
            SET status = ?, error_message = ?, result_json = NULL,
                updated_at = ?, completed_at = ?
            WHERE id = ? AND status = ?
            """,
            (
                JobStatus.FAILED.value,
                error_message,
                _format_dt(now),
                _format_dt(now),
                str(job_id),
                JobStatus.RUNNING.value,
            ),
        )
        if cursor.rowcount != 1:
            raise JobStateError(f"job {job_id} is not running")
        self._connection.commit()
        record = self.get(job_id)
        if record is None:
            raise JobNotFoundError(str(job_id))
        return record

    def cancel_pending(self, job_id: JobId) -> JobRecord:
        now = _utc_now()
        cursor = self._connection.execute(
            """
            UPDATE jobs
            SET status = ?, updated_at = ?, completed_at = ?
            WHERE id = ? AND status = ?
            """,
            (
                JobStatus.CANCELLED.value,
                _format_dt(now),
                _format_dt(now),
                str(job_id),
                JobStatus.PENDING.value,
            ),
        )
        if cursor.rowcount != 1:
            existing = self.get(job_id)
            if existing is None:
                raise JobNotFoundError(str(job_id))
            raise JobStateError(f"job {job_id} is not pending")
        self._connection.commit()
        record = self.get(job_id)
        if record is None:
            raise JobNotFoundError(str(job_id))
        return record

    def retry_failed(self, job_id: JobId) -> JobRecord:
        now = _utc_now()
        cursor = self._connection.execute(
            """
            UPDATE jobs
            SET status = ?, error_message = NULL, result_json = NULL,
                started_at = NULL, completed_at = NULL, updated_at = ?
            WHERE id = ? AND status = ?
            """,
            (
                JobStatus.PENDING.value,
                _format_dt(now),
                str(job_id),
                JobStatus.FAILED.value,
            ),
        )
        if cursor.rowcount != 1:
            existing = self.get(job_id)
            if existing is None:
                raise JobNotFoundError(str(job_id))
            raise JobStateError(f"job {job_id} is not failed")
        self._connection.commit()
        record = self.get(job_id)
        if record is None:
            raise JobNotFoundError(str(job_id))
        return record

    def recover_running_to_pending(self) -> int:
        now = _utc_now()
        cursor = self._connection.execute(
            """
            UPDATE jobs
            SET status = ?, started_at = NULL, updated_at = ?
            WHERE status = ?
            """,
            (
                JobStatus.PENDING.value,
                _format_dt(now),
                JobStatus.RUNNING.value,
            ),
        )
        self._connection.commit()
        return cursor.rowcount

    def prune_completed(self) -> int:
        rows = self._connection.execute(
            """
            SELECT id FROM jobs
            WHERE status = ?
            ORDER BY completed_at DESC, created_at DESC
            """,
            (JobStatus.COMPLETED.value,),
        ).fetchall()
        if len(rows) <= _COMPLETED_RETENTION:
            return 0
        stale_ids = [row["id"] for row in rows[_COMPLETED_RETENTION:]]
        cursor = self._connection.execute(
            f"""
            DELETE FROM jobs
            WHERE id IN ({",".join("?" for _ in stale_ids)})
            """,
            stale_ids,
        )
        self._connection.commit()
        return cursor.rowcount

    def has_pending(self) -> bool:
        row = self._connection.execute(
            "SELECT 1 FROM jobs WHERE status = ? LIMIT 1",
            (JobStatus.PENDING.value,),
        ).fetchone()
        return row is not None
