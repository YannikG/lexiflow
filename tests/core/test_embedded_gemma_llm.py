"""Tests for lexiflow_core.llm.embedded_gemma."""

from __future__ import annotations

from pathlib import Path

import pytest
from lexiflow_core.llm.embedded_gemma import (
    EmbeddedGemmaLLM,
    find_model_dir,
)
from lexiflow_core.models.lockfile import load_models_lock
from lexiflow_core.models.paths import artifact_dir
from lexiflow_core.models.requirements import EMBEDDED_GEMMA_ID


class FakeGemmaGenerator:
    def __init__(self, response: str = "# Titulo\n\ncuerpo") -> None:
        self.response = response
        self.last_prompt: str | None = None

    def generate(self, prompt: str) -> str:
        self.last_prompt = prompt
        return self.response


def test_find_model_dir_requires_config_json(tmp_path: Path) -> None:
    (tmp_path / "revision.txt").write_text("sha", encoding="utf-8")

    with pytest.raises(FileNotFoundError, match="config.json"):
        find_model_dir(tmp_path)


def test_find_model_dir_returns_root_when_valid(tmp_path: Path) -> None:
    (tmp_path / "config.json").write_text("{}", encoding="utf-8")

    assert find_model_dir(tmp_path) == tmp_path


def test_embedded_gemma_complete_uses_generator(tmp_path: Path) -> None:
    lock = load_models_lock()
    artifact = next(a for a in lock.artifacts if a.id == EMBEDDED_GEMMA_ID)
    dest = artifact_dir(tmp_path, EMBEDDED_GEMMA_ID)
    dest.mkdir(parents=True)
    (dest / "revision.txt").write_text(artifact.revision, encoding="utf-8")
    (dest / "config.json").write_text("{}", encoding="utf-8")
    generator = FakeGemmaGenerator("# Titulo\n\ncuerpo")

    llm = EmbeddedGemmaLLM.from_data_root(tmp_path, generator=generator)

    assert llm.complete("prompt") == "# Titulo\n\ncuerpo"
    assert generator.last_prompt == "prompt"
    assert llm.model_dir == dest
