"""Build argv for spawning the worker process."""

from __future__ import annotations

import sys
from pathlib import Path


def build_worker_command(executable: str, data_root: Path) -> list[str]:
    """Return argv to start lexiflow_worker against the given data root."""
    if getattr(sys, "frozen", False):
        return [
            executable,
            "--worker",
            "--data-root",
            str(data_root),
        ]
    return [
        executable,
        "-m",
        "lexiflow_worker",
        "--data-root",
        str(data_root),
    ]
