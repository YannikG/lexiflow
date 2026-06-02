"""Shared types and layout constants for the application shell."""

from __future__ import annotations

from typing import Literal

from lexiflow_core.jobs.models import JobType

NavigationMode = Literal["texts", "vocabulary", "study"]

LLM_JOB_TYPES = frozenset(
    {JobType.CLEANUP, JobType.TRANSLATE, JobType.SIMPLIFY, JobType.LEMMA}
)

DEFAULT_WINDOW_WIDTH = 1200
DEFAULT_WINDOW_HEIGHT = 800
MIN_WINDOW_WIDTH = 800
MIN_WINDOW_HEIGHT = 500
SIDEBAR_WIDTH = 260
