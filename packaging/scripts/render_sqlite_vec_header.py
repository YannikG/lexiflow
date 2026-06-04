"""Generate sqlite-vec.h from upstream sqlite-vec.h.tmpl (tag zips omit the header)."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
from pathlib import Path


def render_sqlite_vec_header(
    source_dir: Path,
    *,
    source_label: str = "lexiflow-packaging",
) -> Path:
    """Write sqlite-vec.h next to sqlite-vec.c; return the header path."""
    version_path = source_dir / "VERSION"
    template_path = source_dir / "sqlite-vec.h.tmpl"
    if not version_path.is_file():
        raise FileNotFoundError(f"VERSION missing under {source_dir}")
    if not template_path.is_file():
        raise FileNotFoundError(f"sqlite-vec.h.tmpl missing under {source_dir}")

    version_text = version_path.read_text(encoding="utf-8").strip()
    parts = version_text.split(".")
    major = parts[0] if parts else "0"
    minor = parts[1] if len(parts) > 1 else "0"
    patch = parts[2].split("-", maxsplit=1)[0] if len(parts) > 2 else "0"
    date = datetime.fromtimestamp(version_path.stat().st_mtime, tz=UTC).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )

    header = template_path.read_text(encoding="utf-8")
    replacements = {
        "VERSION": version_text,
        "DATE": date,
        "SOURCE": source_label,
        "VERSION_MAJOR": major,
        "VERSION_MINOR": minor,
        "VERSION_PATCH": patch,
    }
    for key, value in replacements.items():
        header = header.replace(f"${{{key}}}", value)

    out_path = source_dir / "sqlite-vec.h"
    out_path.write_text(header, encoding="utf-8")
    return out_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "source_dir",
        type=Path,
        help="Extracted sqlite-vec tree (VERSION + sqlite-vec.h.tmpl)",
    )
    args = parser.parse_args()
    path = render_sqlite_vec_header(args.source_dir.resolve())
    print(path)


if __name__ == "__main__":
    main()
