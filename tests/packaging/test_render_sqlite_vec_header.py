"""Tests for sqlite-vec header generation from upstream template."""

from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_render_sqlite_vec_header():
    script = (
        Path(__file__).resolve().parents[2]
        / "packaging"
        / "scripts"
        / "render_sqlite_vec_header.py"
    )
    spec = importlib.util.spec_from_file_location(
        "lexiflow_render_sqlite_vec_header",
        script,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_render_sqlite_vec_header_substitutes_version_fields(tmp_path: Path) -> None:
    render = _load_render_sqlite_vec_header()
    (tmp_path / "VERSION").write_text("0.1.9\n", encoding="utf-8")
    (tmp_path / "sqlite-vec.h.tmpl").write_text(
        '#define SQLITE_VEC_VERSION "v${VERSION}"\n'
        '#define SQLITE_VEC_DATE "${DATE}"\n'
        '#define SQLITE_VEC_SOURCE "${SOURCE}"\n'
        "#define SQLITE_VEC_VERSION_MAJOR ${VERSION_MAJOR}\n"
        "#define SQLITE_VEC_VERSION_MINOR ${VERSION_MINOR}\n"
        "#define SQLITE_VEC_VERSION_PATCH ${VERSION_PATCH}\n",
        encoding="utf-8",
    )

    header_path = render.render_sqlite_vec_header(tmp_path, source_label="test-source")
    text = header_path.read_text(encoding="utf-8")

    assert 'SQLITE_VEC_VERSION "v0.1.9"' in text
    assert 'SQLITE_VEC_SOURCE "test-source"' in text
    assert "SQLITE_VEC_VERSION_MAJOR 0" in text
    assert "SQLITE_VEC_VERSION_MINOR 1" in text
    assert "SQLITE_VEC_VERSION_PATCH 9" in text
    assert "${" not in text
