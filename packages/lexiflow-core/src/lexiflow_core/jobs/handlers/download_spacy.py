"""spaCy language pack download job handler."""

from __future__ import annotations

from pathlib import Path

from lexiflow_core.jobs.models import JobRecord
from lexiflow_core.jobs.service import JobService
from lexiflow_core.languages.spacy_pack import SpacyPackError, install_spacy_pack
from lexiflow_core.vocabulary.lemma_resolution import (
    spacy_pack_available,
    spacy_pack_dir,
)


def _iso_from_payload(job: JobRecord) -> str:
    payload = job.payload or {}
    iso = payload.get("iso")
    if not isinstance(iso, str) or not iso.strip():
        raise ValueError(f"job {job.id} is missing iso")
    return iso.strip()


def handle_download_spacy(
    job: JobRecord,
    *,
    data_root: Path,
    job_service: JobService,
) -> None:
    """Download and export a spaCy pack for the target language in the job payload."""
    try:
        iso = _iso_from_payload(job)
    except ValueError as exc:
        job_service.fail(job.id, str(exc))
        return

    if spacy_pack_available(data_root, iso):
        pack_dir = spacy_pack_dir(data_root, iso)
        job_service.complete(
            job.id,
            {"iso": iso, "pack_dir": str(pack_dir), "skipped": True},
        )
        return

    try:
        pack_dir = install_spacy_pack(data_root, iso)
    except SpacyPackError as exc:
        job_service.fail(job.id, str(exc))
        return
    except Exception as exc:
        job_service.fail(job.id, str(exc))
        return

    job_service.complete(job.id, {"iso": iso, "pack_dir": str(pack_dir)})
