"""Module entrypoint for `python -m lexiflow_worker`."""

from __future__ import annotations

from lexiflow_core.db.sqlite_bootstrap import ensure_loadable_sqlite3

ensure_loadable_sqlite3()

from lexiflow_worker.main import main

if __name__ == "__main__":
    raise SystemExit(main())
