"""Library backup export and restore."""

from __future__ import annotations

import json
import shutil
import tempfile
import zipfile
from datetime import UTC, datetime
from pathlib import Path

EXPORT_FORMAT = "lexiflow-library"
EXPORT_VERSION = 1


def export_library_zip(destination: Path, *, data_root: Path) -> Path:
    """Write a zip archive of the entire data root."""
    root = data_root.expanduser().resolve()
    if not root.is_dir():
        raise FileNotFoundError(f"data root not found: {root}")
    destination = destination.expanduser().resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    manifest = {
        "format": EXPORT_FORMAT,
        "version": EXPORT_VERSION,
        "exported_at": datetime.now(UTC).isoformat(),
    }
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(
            "manifest.json",
            json.dumps(manifest, indent=2) + "\n",
        )
        for path in sorted(root.rglob("*")):
            if not path.is_file():
                continue
            archive.write(path, arcname=str(path.relative_to(root)))
    return destination


def restore_library_zip(
    archive_path: Path,
    *,
    destination_root: Path,
) -> Path:
    """Extract a library backup zip into a destination data root."""
    archive = archive_path.expanduser().resolve()
    if not archive.is_file():
        raise FileNotFoundError(f"backup archive not found: {archive}")
    destination = destination_root.expanduser().resolve()
    destination.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        with zipfile.ZipFile(archive, "r") as zf:
            zf.extractall(temp_root)
        manifest_path = temp_root / "manifest.json"
        if not manifest_path.is_file():
            raise ValueError("backup archive missing manifest.json")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("format") != EXPORT_FORMAT:
            raise ValueError("unsupported backup format")
        for path in temp_root.rglob("*"):
            if path.is_dir():
                continue
            if path.name == "manifest.json" and path.parent == temp_root:
                continue
            relative = path.relative_to(temp_root)
            target = destination / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)
    return destination


def replace_data_root_from_zip(
    archive_path: Path,
    *,
    data_root: Path,
) -> None:
    """Replace the current data root contents from a backup zip."""
    root = data_root.expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    for child in list(root.iterdir()):
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink()
    restore_library_zip(archive_path, destination_root=root)
