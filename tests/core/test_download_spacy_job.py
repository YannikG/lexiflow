"""Tests for download_spacy background jobs."""

from __future__ import annotations

from pathlib import Path

from lexiflow_core.jobs.handlers.download_spacy import handle_download_spacy
from lexiflow_core.jobs.models import JobRequest, JobStatus, JobType
from lexiflow_core.jobs.runner import run_worker_loop
from lexiflow_core.jobs.service import JobService
from lexiflow_core.languages.setup import add_target_with_spacy_download
from lexiflow_core.languages.spacy_pack import spacy_model_name
from lexiflow_core.llm.fake import FakeLLM
from lexiflow_core.vocabulary.lemma_resolution import spacy_pack_dir


def test_spacy_model_name_uses_special_case_for_chinese() -> None:
    assert spacy_model_name("zh") == "zh_core_web_sm"
    assert spacy_model_name("es") == "es_core_news_sm"


def test_download_spacy_job_completes_with_injected_install(
    tmp_path: Path, monkeypatch
) -> None:
    data_root = tmp_path / "LexiFlow"
    job_service = JobService(data_root)
    job_id = job_service.enqueue(
        JobRequest(job_type=JobType.DOWNLOAD_SPACY, payload={"iso": "es"})
    )
    claimed = job_service.claim_next()
    assert claimed is not None
    assert claimed.id == job_id

    def fake_install(_data_root: Path, iso: str) -> Path:
        pack_dir = spacy_pack_dir(_data_root, iso)
        pack_dir.mkdir(parents=True, exist_ok=True)
        (pack_dir / "meta.json").write_text("{}")
        return pack_dir

    monkeypatch.setattr(
        "lexiflow_core.jobs.handlers.download_spacy.install_spacy_pack",
        fake_install,
    )

    handle_download_spacy(
        claimed,
        data_root=data_root,
        job_service=job_service,
    )

    updated = job_service.get(job_id)
    assert updated is not None
    assert updated.status == JobStatus.COMPLETED
    assert updated.result is not None
    assert updated.result["iso"] == "es"
    assert spacy_pack_dir(data_root, "es").is_dir()


def test_download_spacy_skips_when_pack_already_installed(tmp_path: Path) -> None:
    data_root = tmp_path / "LexiFlow"
    pack_dir = spacy_pack_dir(data_root, "es")
    pack_dir.mkdir(parents=True)
    (pack_dir / "meta.json").write_text("{}")

    job_service = JobService(data_root)
    job_id = job_service.enqueue(
        JobRequest(job_type=JobType.DOWNLOAD_SPACY, payload={"iso": "es"})
    )
    claimed = job_service.claim_next()
    assert claimed is not None

    handle_download_spacy(claimed, data_root=data_root, job_service=job_service)

    updated = job_service.get(job_id)
    assert updated is not None
    assert updated.status == JobStatus.COMPLETED
    assert updated.result is not None
    assert updated.result.get("skipped") is True


def test_worker_runs_download_spacy_job(tmp_path: Path, monkeypatch) -> None:
    data_root = tmp_path / "LexiFlow"

    def fake_install(_data_root: Path, iso: str) -> Path:
        pack_dir = spacy_pack_dir(_data_root, iso)
        pack_dir.mkdir(parents=True, exist_ok=True)
        (pack_dir / "meta.json").write_text("{}")
        return pack_dir

    monkeypatch.setattr(
        "lexiflow_core.jobs.handlers.download_spacy.install_spacy_pack",
        fake_install,
    )

    add_target_with_spacy_download(data_root, "es")
    job_service = JobService(data_root)
    jobs = [job for job in job_service.list_jobs() if job.status == JobStatus.PENDING]
    assert len(jobs) == 1
    assert jobs[0].job_type == JobType.DOWNLOAD_SPACY

    run_worker_loop(job_service, FakeLLM(response="unused"), data_root=data_root)

    completed = job_service.list_jobs()[0]
    assert completed.status == JobStatus.COMPLETED
    assert completed.error_message is None
