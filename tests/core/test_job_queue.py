"""Tests for the persistent job queue and worker loop."""

from __future__ import annotations

import json
import threading
import time
from pathlib import Path
from uuid import uuid4

import pytest
from lexiflow_core.config.paths import queue_db_path
from lexiflow_core.db.connection import connect_sqlite
from lexiflow_core.db.migration_loader import queue_migrations_dir
from lexiflow_core.jobs.models import JobRequest, JobStatus, JobType
from lexiflow_core.jobs.runner import run_worker_loop
from lexiflow_core.jobs.service import JobService
from lexiflow_core.jobs.store import JobStateError
from lexiflow_core.llm.fake import FakeLLM


@pytest.fixture
def data_root(tmp_path: Path) -> Path:
    return tmp_path / "LexiFlow"


@pytest.fixture
def job_service(data_root: Path) -> JobService:
    return JobService(data_root)


def _enqueue_prompt(job_service: JobService, prompt: str) -> None:
    job_service.enqueue(
        JobRequest(job_type=JobType.TRANSLATE, payload={"prompt": prompt})
    )


def test_enqueue_persists_pending_job(job_service: JobService) -> None:
    job_id = job_service.enqueue(
        JobRequest(job_type=JobType.CLEANUP, payload={"prompt": "hello"})
    )

    jobs = job_service.list_jobs()
    assert len(jobs) == 1
    assert jobs[0].id == job_id
    assert jobs[0].status == JobStatus.PENDING
    assert jobs[0].payload == {"prompt": "hello"}


def test_worker_completes_job_with_fake_llm(job_service: JobService) -> None:
    _enqueue_prompt(job_service, "translate this")

    run_worker_loop(job_service, FakeLLM(response="done text"))

    jobs = job_service.list_jobs()
    assert len(jobs) == 1
    assert jobs[0].status == JobStatus.COMPLETED
    assert jobs[0].result == {"text": "done text"}


def test_only_one_job_runs_at_a_time(job_service: JobService) -> None:
    _enqueue_prompt(job_service, "first")
    _enqueue_prompt(job_service, "second")
    llm = FakeLLM(response="ok", block_on_call=1)

    worker = threading.Thread(target=run_worker_loop, args=(job_service, llm))
    worker.start()
    assert llm.wait_blocked()

    jobs = job_service.list_jobs(limit=10)
    statuses = {job.status for job in jobs}
    assert JobStatus.RUNNING in statuses
    assert JobStatus.PENDING in statuses
    assert sum(job.status == JobStatus.RUNNING for job in jobs) == 1

    llm.unblock()
    worker.join(timeout=5)
    assert not worker.is_alive()

    jobs = job_service.list_jobs(limit=10)
    assert all(job.status == JobStatus.COMPLETED for job in jobs)


def test_claim_next_refuses_while_another_job_is_running(
    job_service: JobService,
) -> None:
    _enqueue_prompt(job_service, "first")
    _enqueue_prompt(job_service, "second")

    first = job_service.claim_next()
    second = job_service.claim_next()

    assert first is not None
    assert second is None
    jobs = job_service.list_jobs(limit=10)
    running = [job for job in jobs if job.status == JobStatus.RUNNING]
    assert len(running) == 1
    assert running[0].id == first.id


def test_failure_marks_failed_without_crashing_worker(
    job_service: JobService,
) -> None:
    _enqueue_prompt(job_service, "boom")
    _enqueue_prompt(job_service, "recover")

    run_worker_loop(
        job_service,
        FakeLLM(response="ok", error=RuntimeError("llm exploded")),
    )

    jobs = {job.payload["prompt"]: job for job in job_service.list_jobs(limit=10)}
    assert jobs["boom"].status == JobStatus.FAILED
    assert jobs["boom"].error_message == "llm exploded"
    assert jobs["recover"].status == JobStatus.COMPLETED
    assert jobs["recover"].result == {"text": "ok"}


def test_cancel_pending_job_never_runs(job_service: JobService) -> None:
    job_id = job_service.enqueue(
        JobRequest(job_type=JobType.TRANSLATE, payload={"prompt": "skip me"})
    )

    job_service.cancel(job_id)
    run_worker_loop(job_service, FakeLLM(response="should not run"))

    jobs = job_service.list_jobs()
    assert len(jobs) == 1
    assert jobs[0].status == JobStatus.CANCELLED
    assert jobs[0].result is None


def test_worker_loop_recovers_interrupted_running_job(job_service: JobService) -> None:
    job_id = uuid4()
    connection = connect_sqlite(job_service.db_path)
    try:
        connection.execute(
            """
            INSERT INTO jobs (
                id, job_type, status, payload_json, created_at, updated_at,
                started_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(job_id),
                JobType.TRANSLATE.value,
                JobStatus.RUNNING.value,
                json.dumps({"prompt": "resume via loop"}),
                "2026-01-01T00:00:00.000000Z",
                "2026-01-01T00:00:00.000000Z",
                "2026-01-01T00:00:01.000000Z",
            ),
        )
        connection.commit()
    finally:
        connection.close()

    run_worker_loop(job_service, FakeLLM(response="done"))

    jobs = job_service.list_jobs()
    assert len(jobs) == 1
    assert jobs[0].id == job_id
    assert jobs[0].status == JobStatus.COMPLETED
    assert jobs[0].result == {"text": "done"}


def test_recover_on_startup_moves_running_to_pending(
    job_service: JobService, data_root: Path
) -> None:
    job_id = uuid4()
    connection = connect_sqlite(queue_db_path(data_root))
    try:
        connection.execute(
            """
            INSERT INTO jobs (
                id, job_type, status, payload_json, created_at, updated_at,
                started_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(job_id),
                JobType.TRANSLATE.value,
                JobStatus.RUNNING.value,
                json.dumps({"prompt": "resume me"}),
                "2026-01-01T00:00:00.000000Z",
                "2026-01-01T00:00:00.000000Z",
                "2026-01-01T00:00:01.000000Z",
            ),
        )
        connection.commit()
    finally:
        connection.close()

    job_service.recover_on_startup()

    jobs = job_service.list_jobs()
    assert len(jobs) == 1
    assert jobs[0].id == job_id
    assert jobs[0].status == JobStatus.PENDING
    assert jobs[0].started_at is None


def test_list_jobs_prunes_completed_beyond_twenty(job_service: JobService) -> None:
    for index in range(25):
        job_id = job_service.enqueue(
            JobRequest(
                job_type=JobType.EMBED,
                payload={"prompt": f"job-{index}"},
            )
        )
        claimed = job_service.claim_next()
        assert claimed is not None
        assert claimed.id == job_id
        job_service.complete(job_id, {"text": f"result-{index}"})
        time.sleep(0.001)

    jobs = job_service.list_jobs(limit=100)
    completed = [job for job in jobs if job.status == JobStatus.COMPLETED]
    assert len(completed) == 20
    kept_indexes = {int(job.payload["prompt"].split("-")[1]) for job in completed}
    assert kept_indexes == set(range(5, 25))


def test_missing_prompt_marks_job_failed(job_service: JobService) -> None:
    job_service.enqueue(JobRequest(job_type=JobType.CLEANUP, payload={}))

    run_worker_loop(job_service, FakeLLM(response="unused"))

    jobs = job_service.list_jobs()
    assert len(jobs) == 1
    assert jobs[0].status == JobStatus.FAILED
    assert "missing a string prompt" in (jobs[0].error_message or "")


def test_cancel_running_job_raises(job_service: JobService) -> None:
    job_id = job_service.enqueue(
        JobRequest(job_type=JobType.TRANSLATE, payload={"prompt": "running"})
    )
    claimed = job_service.claim_next()
    assert claimed is not None

    with pytest.raises(JobStateError):
        job_service.cancel(job_id)


def test_retry_pending_job_raises(job_service: JobService) -> None:
    job_id = job_service.enqueue(
        JobRequest(job_type=JobType.TRANSLATE, payload={"prompt": "pending"})
    )

    with pytest.raises(JobStateError):
        job_service.retry(job_id)


def test_retry_failed_job_completes_on_next_worker_tick(
    job_service: JobService,
) -> None:
    job_id = job_service.enqueue(
        JobRequest(job_type=JobType.SIMPLIFY, payload={"prompt": "retry me"})
    )
    claimed = job_service.claim_next()
    assert claimed is not None
    job_service.fail(job_id, "temporary")

    job_service.retry(job_id)
    run_worker_loop(job_service, FakeLLM(response="fixed"))

    jobs = job_service.list_jobs()
    assert len(jobs) == 1
    assert jobs[0].status == JobStatus.COMPLETED
    assert jobs[0].result == {"text": "fixed"}


def test_recover_on_startup_does_not_retry_failed_jobs(
    job_service: JobService, data_root: Path
) -> None:
    job_id = uuid4()
    connection = connect_sqlite(queue_db_path(data_root))
    try:
        connection.execute(
            """
            INSERT INTO jobs (
                id, job_type, status, payload_json, created_at, updated_at,
                error_message, completed_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(job_id),
                JobType.TRANSLATE.value,
                JobStatus.FAILED.value,
                json.dumps({"prompt": "stay failed"}),
                "2026-01-01T00:00:00.000000Z",
                "2026-01-01T00:00:00.000000Z",
                "still broken",
                "2026-01-01T00:00:01.000000Z",
            ),
        )
        connection.commit()
    finally:
        connection.close()

    job_service.recover_on_startup()
    run_worker_loop(job_service, FakeLLM(response="nope"))

    jobs = job_service.list_jobs()
    assert len(jobs) == 1
    assert jobs[0].status == JobStatus.FAILED
    assert jobs[0].error_message == "still broken"


def test_queue_migrations_dir_contains_initial_script() -> None:
    migrations_dir = queue_migrations_dir()

    assert migrations_dir.is_dir()
    assert (migrations_dir / "001_initial.sql").is_file()


def test_fail_running_job_requires_running_state(job_service: JobService) -> None:
    job_id = job_service.enqueue(
        JobRequest(job_type=JobType.CLEANUP, payload={"prompt": "pending"})
    )

    with pytest.raises(JobStateError):
        job_service.fail(job_id, "not running yet")
