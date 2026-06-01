"""Coordinate llama-server and worker startup for AI jobs."""

from __future__ import annotations

from lexiflow_ui.llama_server_supervisor import LlamaServerSupervisor
from lexiflow_ui.worker_supervisor import WorkerSupervisor


def ensure_ai_workers_running(
    worker_supervisor: WorkerSupervisor,
    llama_supervisor: LlamaServerSupervisor | None,
) -> None:
    """Start llama-server when needed, then spawn the worker once inference is ready."""
    if llama_supervisor is not None:
        llama_supervisor.ensure_running()
        if not llama_supervisor.is_ready():
            return
    worker_supervisor.ensure_running()
