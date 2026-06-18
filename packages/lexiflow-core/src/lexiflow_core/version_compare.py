"""Shared version string parsing and comparison."""

from __future__ import annotations

import re

_SEMVER_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")


def version_parts(value: str) -> tuple[int, ...]:
    """Extract numeric segments from a version string for ordering."""
    parts = re.findall(r"\d+", value)
    return tuple(int(part) for part in parts) if parts else (0,)


def _semver_triple(parts: tuple[int, ...]) -> tuple[int, int, int]:
    padded = (*parts, 0, 0, 0)
    return padded[0], padded[1], padded[2]


def is_newer_version(installed: str, latest: str) -> bool:
    installed_parts = version_parts(installed)
    latest_parts = version_parts(latest)
    installed_triple = _semver_triple(installed_parts)
    latest_triple = _semver_triple(latest_parts)
    if latest_triple != installed_triple:
        return latest_triple > installed_triple
    # Same X.Y.Z: release beats dev/pre-release suffix segments.
    return len(latest_parts) < len(installed_parts)


def parse_semver_triple(version: str) -> tuple[int, int, int]:
    """Parse ``X.Y.Z``; raise ``ValueError`` when not a plain semver triple."""
    match = _SEMVER_RE.match(version.strip())
    if match is None:
        raise ValueError(f"not a semver triple: {version!r}")
    return int(match.group(1)), int(match.group(2)), int(match.group(3))


def semver_to_str(parts: tuple[int, int, int]) -> str:
    return f"{parts[0]}.{parts[1]}.{parts[2]}"


def semver_max(*versions: str) -> str:
    """Return the greatest ``X.Y.Z`` among the given versions."""
    if not versions:
        raise ValueError("semver_max requires at least one version")
    return semver_to_str(max(parse_semver_triple(version) for version in versions))


def bump_semver(version: str, bump: str) -> str:
    """Return ``version`` after applying ``patch``, ``minor``, or ``major``."""
    major, minor, patch = parse_semver_triple(version)
    if bump == "patch":
        return semver_to_str((major, minor, patch + 1))
    if bump == "minor":
        return semver_to_str((major, minor + 1, 0))
    if bump == "major":
        return semver_to_str((major + 1, 0, 0))
    raise ValueError(f"unsupported bump: {bump!r}")
