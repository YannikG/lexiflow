"""Release bundle dependency constraints."""

from __future__ import annotations

from pathlib import Path


def test_release_group_excludes_sentence_transformers_and_torch() -> None:
    root = Path(__file__).resolve().parents[2]
    lock_text = (root / "uv.lock").read_text(encoding="utf-8")
    pyproject = (root / "pyproject.toml").read_text(encoding="utf-8")

    assert "sentence-transformers" not in pyproject
    assert 'name = "sentence-transformers"' not in lock_text
    assert 'name = "torch"' not in lock_text
    spec = (root / "packaging" / "lexiflow.spec").read_text(encoding="utf-8")
    assert "sentence_transformers" not in spec
    assert "sklearn" not in spec
    assert "sqlite_bootstrap" in spec
    assert "sqlean" in spec or 'sys.platform != "win32"' in spec
    assert "_sqlite_vec_binaries" in spec
    assert "VENDOR_VEC_DIR" in spec
    assert "_host_vec0_filenames" in spec
