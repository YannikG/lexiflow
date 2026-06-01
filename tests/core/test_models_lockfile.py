"""Tests for bundled models.lock."""

from __future__ import annotations

from pathlib import Path

from lexiflow_core.models.lockfile import load_models_lock


def test_load_models_lock_parses_llama_hf_model(tmp_path: Path) -> None:
    lock_path = tmp_path / "models.lock"
    lock_path.write_text(
        """
[[artifacts]]
id = "embedding-minilm"
repo = "sentence-transformers/all-MiniLM-L6-v2"
revision = "c9745ed1d9f207416be6d2e6f8de32d1f16199bf"

[[artifacts]]
id = "native-llm"
repo = "ggml-org/gemma-4-E2B-it-GGUF"
revision = "a1dac71d3ab220618f5a7573a52acdc4baf3ae3b"
llama_hf_model = "ggml-org/gemma-4-E2B-it-GGUF:Q8_0"
""".strip(),
        encoding="utf-8",
    )

    lock = load_models_lock(lock_path)

    assert len(lock.artifacts) == 2
    assert lock.artifacts[1].id == "native-llm"
    assert lock.artifacts[1].llama_hf_model == (
        "ggml-org/gemma-4-E2B-it-GGUF:Q8_0"
    )


def test_bundled_models_lock_loads_two_artifacts() -> None:
    from lexiflow_core.models.lockfile import bundled_models_lock_path

    lock = load_models_lock(bundled_models_lock_path())

    assert len(lock.artifacts) >= 2
    for artifact in lock.artifacts:
        assert artifact.id
        assert artifact.repo
        assert artifact.revision


def test_bundled_native_llm_has_llama_hf_model_pin() -> None:
    from lexiflow_core.models.lockfile import bundled_models_lock_path

    lock = load_models_lock(bundled_models_lock_path())
    native = next(a for a in lock.artifacts if a.id == "native-llm")

    assert native.llama_hf_model
    assert ":" in native.llama_hf_model
