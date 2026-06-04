"""Normalize LexiFlow build versions for WiX Product/@Version."""

from __future__ import annotations

import argparse
import os
import re


def normalize_wix_product_version(raw: str) -> str:
    """Return a four-part numeric version string accepted by WiX."""
    prefix = re.split(r"[^0-9.]", raw.strip(), maxsplit=1)[0].strip(".")
    match = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)(?:\.(\d+))?", prefix)
    if match is not None:
        major, minor, patch, build = match.groups()
        if build is not None:
            return f"{major}.{minor}.{patch}.{build}"
        return f"{major}.{minor}.{patch}.0"
    sanitized = re.sub(r"[^0-9.]", "", raw)
    parts = [part for part in sanitized.split(".") if part != ""][:3]
    while len(parts) < 3:
        parts.append("0")
    return ".".join([*parts, "0"])


def resolve_wix_product_version() -> str:
    """Read WIX_VERSION, LF_VERSION, or fall back to 0.0.0.0."""
    raw = os.environ.get("WIX_VERSION") or os.environ.get("LF_VERSION") or "0.0.0.0"
    return normalize_wix_product_version(raw)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Print WiX Product version")
    parser.add_argument(
        "raw",
        nargs="?",
        help="Optional raw version; otherwise read WIX_VERSION/LF_VERSION env",
    )
    args = parser.parse_args(argv)
    version = (
        normalize_wix_product_version(args.raw)
        if args.raw is not None
        else resolve_wix_product_version()
    )
    print(version)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
