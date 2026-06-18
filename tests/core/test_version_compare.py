"""Tests for shared version comparison helpers."""

from __future__ import annotations

from lexiflow_core.version_compare import is_newer_version, parse_semver_triple


def test_is_newer_version_compares_numeric_segments() -> None:
    assert is_newer_version("1.0.0", "1.0.1")
    assert not is_newer_version("1.2.0", "1.1.9")
    assert is_newer_version("1.0.6", "1.0.7.dev42")


def test_parse_semver_triple_rejects_suffix_without_third_segment() -> None:
    try:
        parse_semver_triple("1.0.7.dev42")
    except ValueError as exc:
        assert "not a semver triple" in str(exc)
    else:
        raise AssertionError("expected ValueError")
