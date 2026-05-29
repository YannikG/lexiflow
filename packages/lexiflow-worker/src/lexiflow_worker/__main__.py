"""Worker process entrypoint."""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def main() -> int:
    logger.info("worker ready")
    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    raise SystemExit(main())
