"""Tests for lexiflow_worker.runner re-export."""

from __future__ import annotations

from lexiflow_worker.runner import run_worker_loop


def test_runner_reexports_core_loop() -> None:
    assert run_worker_loop is not None
    assert run_worker_loop.__module__ == "lexiflow_core.jobs.runner"
