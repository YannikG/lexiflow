"""Tests for text slug generation."""

from __future__ import annotations

from lexiflow_core.library.slug import make_text_slug


def test_make_text_slug_uses_title_and_suffix() -> None:
    assert make_text_slug("El País", suffix="a3f2") == "el-pa-s-a3f2"


def test_make_text_slug_generates_suffix_when_missing() -> None:
    slug = make_text_slug("Article")

    assert slug.startswith("article-")
    assert len(slug) > len("article-")
