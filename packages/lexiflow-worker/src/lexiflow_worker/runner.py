"""Thin re-export of the core worker loop for the worker package entrypoint."""

from __future__ import annotations

from lexiflow_core.jobs.runner import run_worker_loop

__all__ = ["run_worker_loop"]
