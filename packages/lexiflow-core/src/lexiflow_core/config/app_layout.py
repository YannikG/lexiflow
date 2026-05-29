"""Filesystem layout creation under the user library data root."""

from __future__ import annotations

from pathlib import Path


def ensure_app_layout(data_root: Path) -> None:
    """Create runtime directories under the user library data root."""
    (data_root / ".app").mkdir(parents=True, exist_ok=True)
    (data_root / ".app" / "logs").mkdir(parents=True, exist_ok=True)
    (data_root / ".app" / "models").mkdir(parents=True, exist_ok=True)
