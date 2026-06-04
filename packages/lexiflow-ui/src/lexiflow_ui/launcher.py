"""Unified CLI entrypoint for LexiFlow (dev, PyInstaller bundle)."""

from __future__ import annotations

import argparse
import sys

import lexiflow_core
from lexiflow_worker.main import main as _worker_main

from lexiflow_ui.app import run as _ui_run


def main(argv: list[str] | None = None) -> int:
    """Dispatch to UI, worker, or print version."""
    if argv is None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser(prog="lexiflow", add_help=False)
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--version", action="store_true")
    args, remainder = parser.parse_known_args(argv)

    if args.version:
        print(lexiflow_core.__version__)
        return 0
    if args.worker:
        return _worker_main(remainder)
    return _ui_run(argv)


if __name__ == "__main__":
    raise SystemExit(main())
