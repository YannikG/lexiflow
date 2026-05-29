"""Module entrypoint for `python -m lexiflow_worker`."""

from __future__ import annotations

import logging

from lexiflow_worker.main import main

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    raise SystemExit(main())
