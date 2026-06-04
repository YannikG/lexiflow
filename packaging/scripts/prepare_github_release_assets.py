"""Prepare merged release files for GitHub Releases (2 GiB per-asset limit)."""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

# GitHub release asset API limit; leave headroom for metadata overhead.
GITHUB_RELEASE_MAX_BYTES = 2_147_483_648 - 1_048_576


def asset_needs_compression(
    size_bytes: int,
    *,
    max_bytes: int = GITHUB_RELEASE_MAX_BYTES,
) -> bool:
    """Return True when a file exceeds the GitHub release asset size limit."""
    return size_bytes >= max_bytes


def compress_for_github_release(path: Path) -> Path:
    """Compress ``path`` with zstd and remove the original. Return the ``.zst`` path."""
    if not path.is_file():
        raise FileNotFoundError(path)
    destination = path.with_suffix(path.suffix + ".zst")
    subprocess.run(
        ["zstd", "-T0", "-19", "-f", str(path), "-o", str(destination)],
        check=True,
    )
    path.unlink()
    return destination


def prepare_directory(directory: Path) -> list[Path]:
    """Compress oversized installers in ``directory``; return paths ready to upload."""
    prepared: list[Path] = []
    for candidate in sorted(directory.iterdir()):
        if not candidate.is_file() or candidate.name == "checksums.txt":
            continue
        if asset_needs_compression(candidate.stat().st_size):
            prepared.append(compress_for_github_release(candidate))
        else:
            prepared.append(candidate)
    checksums = directory / "checksums.txt"
    lines = []
    for path in prepared:
        digest = subprocess.check_output(["sha256sum", str(path)], text=True).split()[0]
        lines.append(f"{digest}  {path.name}")
    checksums.write_text("".join(f"{line}\n" for line in lines), encoding="utf-8")
    prepared.append(checksums)
    return prepared


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "merged_dir",
        type=Path,
        help="Directory with release artifacts (e.g. merged/)",
    )
    args = parser.parse_args(argv)
    prepare_directory(args.merged_dir.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
