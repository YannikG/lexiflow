"""Worker process entrypoint."""

from __future__ import annotations

import argparse
import logging
import tempfile
from pathlib import Path

from lexiflow_core.jobs.service import JobService
from lexiflow_core.llm.fake import FakeLLM

from lexiflow_worker.runner import run_worker_loop

logger = logging.getLogger(__name__)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="LexiFlow background worker")
    parser.add_argument(
        "--data-root",
        type=Path,
        default=None,
        help="User library data root containing queue.sqlite",
    )
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO)

    data_root = args.data_root
    temp_dir: tempfile.TemporaryDirectory[str] | None = None
    if data_root is None:
        temp_dir = tempfile.TemporaryDirectory(prefix="lexiflow-worker-")
        data_root = Path(temp_dir.name)

    try:
        job_service = JobService(data_root)
        logger.info("worker consuming queue at %s", job_service.db_path)
        run_worker_loop(job_service, FakeLLM())
        logger.info("worker idle")
    finally:
        if temp_dir is not None:
            temp_dir.cleanup()
    return 0
