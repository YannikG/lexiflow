"""Tests for lexiflow_core.llm.resolution."""

from __future__ import annotations

from pathlib import Path

from lexiflow_core.config.settings import Settings
from lexiflow_core.llm.disabled import DisabledLLM
from lexiflow_core.llm.embedded_gemma import EmbeddedGemmaLLM
from lexiflow_core.llm.ollama import OllamaLLM
from lexiflow_core.llm.resolution import resolve_llm
from lexiflow_core.llm.unavailable import UnavailableLLM
from lexiflow_core.models.lockfile import load_models_lock
from lexiflow_core.models.paths import artifact_dir
from lexiflow_core.models.requirements import EMBEDDED_GEMMA_ID


def test_resolve_llm_returns_ollama_when_url_set(tmp_path: Path) -> None:
    settings = Settings(ollama_url="http://127.0.0.1:11434/")

    provider = resolve_llm(settings, tmp_path)

    assert isinstance(provider, OllamaLLM)
    assert provider.base_url == "http://127.0.0.1:11434"


def test_resolve_llm_returns_disabled_when_llm_off(tmp_path: Path) -> None:
    settings = Settings(llm_enabled=False, ollama_url="http://127.0.0.1:11434")

    provider = resolve_llm(settings, tmp_path)

    assert isinstance(provider, DisabledLLM)


def test_resolve_llm_returns_embedded_when_gemma_installed(tmp_path: Path) -> None:
    lock = load_models_lock()
    artifact = next(a for a in lock.artifacts if a.id == EMBEDDED_GEMMA_ID)
    dest = artifact_dir(tmp_path, EMBEDDED_GEMMA_ID)
    dest.mkdir(parents=True)
    (dest / "revision.txt").write_text(artifact.revision, encoding="utf-8")
    (dest / "config.json").write_text("{}", encoding="utf-8")

    provider = resolve_llm(Settings(), tmp_path)

    assert isinstance(provider, EmbeddedGemmaLLM)


def test_embedded_gemma_installed_requires_config_json(tmp_path: Path) -> None:
    from lexiflow_core.llm.embedded_gemma import embedded_gemma_installed
    from lexiflow_core.models.lockfile import load_models_lock
    from lexiflow_core.models.paths import artifact_dir, artifact_revision_path

    lock = load_models_lock()
    artifact = next(a for a in lock.artifacts if a.id == EMBEDDED_GEMMA_ID)
    dest = artifact_dir(tmp_path, EMBEDDED_GEMMA_ID)
    dest.mkdir(parents=True)
    artifact_revision_path(tmp_path, EMBEDDED_GEMMA_ID).write_text(
        artifact.revision, encoding="utf-8"
    )

    assert embedded_gemma_installed(tmp_path) is False

    (dest / "config.json").write_text("{}", encoding="utf-8")
    assert embedded_gemma_installed(tmp_path) is True


def test_resolve_llm_returns_unavailable_when_no_ollama_and_gemma_missing(
    tmp_path: Path,
) -> None:
    provider = resolve_llm(Settings(), tmp_path)

    assert isinstance(provider, UnavailableLLM)
