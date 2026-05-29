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
    if data_root is None:
        data_root = Path(tempfile.mkdtemp(prefix="lexiflow-worker-"))

    job_service = JobService(data_root)
    logger.info("worker consuming queue at %s", job_service.db_path)
    run_worker_loop(job_service, FakeLLM())
    logger.info("worker idle")
    return 0
