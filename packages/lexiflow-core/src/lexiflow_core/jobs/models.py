"""Domain types for the persistent job queue."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID


class JobType(StrEnum):
    CLEANUP = "cleanup"
    TRANSLATE = "translate"
    SIMPLIFY = "simplify"
    EMBED = "embed"
    DOWNLOAD_SPACY = "download_spacy"


class JobStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


JobId = UUID


@dataclass(frozen=True)
class JobRequest:
    job_type: JobType
    payload: dict[str, Any]


@dataclass(frozen=True)
class JobRecord:
    id: JobId
    job_type: JobType
    status: JobStatus
    payload: dict[str, Any]
    result: dict[str, Any] | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
