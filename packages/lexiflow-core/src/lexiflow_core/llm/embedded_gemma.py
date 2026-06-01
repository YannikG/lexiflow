"""Embedded Gemma 4 E2B: official Google weights, inference in a child process."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Protocol

from lexiflow_core.models.lockfile import load_models_lock
from lexiflow_core.models.paths import artifact_dir, artifact_revision_path
from lexiflow_core.models.requirements import EMBEDDED_GEMMA_ID

_GEMMA_INFERENCE_MODULE = "lexiflow_core.llm.gemma_inference"
_MODEL_DIR_ENV = "LEXIFLOW_GEMMA_MODEL_DIR"


class GemmaGenerator(Protocol):
    def generate(self, prompt: str) -> str: ...


class SubprocessGemmaGenerator:
    """Spawn an isolated Python child to run transformers on google/gemma-4-E2B-it."""

    def __init__(self, model_dir: Path, *, timeout_seconds: float = 600.0) -> None:
        self._model_dir = model_dir
        self._timeout_seconds = timeout_seconds

    def generate(self, prompt: str) -> str:
        env = {**os.environ, _MODEL_DIR_ENV: str(self._model_dir)}
        try:
            completed = subprocess.run(
                [sys.executable, "-m", _GEMMA_INFERENCE_MODULE],
                input=prompt,
                capture_output=True,
                text=True,
                env=env,
                timeout=self._timeout_seconds,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError("Gemma inference subprocess timed out") from exc
        if completed.returncode != 0:
            stderr = completed.stderr.strip() or "unknown error"
            raise RuntimeError(
                f"Gemma inference subprocess failed (exit {completed.returncode}): "
                f"{stderr}"
            )
        output = completed.stdout
        if not output:
            raise RuntimeError("Gemma inference subprocess returned empty output")
        return output


def find_model_dir(artifact_root: Path) -> Path:
    """Return the installed official Gemma artifact directory."""
    if not artifact_root.is_dir():
        raise FileNotFoundError(
            f"{EMBEDDED_GEMMA_ID} is not installed under {artifact_root.parent}. "
            "Complete model bootstrap first."
        )
    if not (artifact_root / "config.json").is_file():
        raise FileNotFoundError(
            f"incomplete {EMBEDDED_GEMMA_ID} install at {artifact_root}: "
            "missing config.json from google/gemma-4-E2B-it"
        )
    return artifact_root


class EmbeddedGemmaLLM:
    def __init__(
        self,
        *,
        model_dir: Path,
        generator: GemmaGenerator | None = None,
    ) -> None:
        self._model_dir = model_dir
        self._generator = (
            generator if generator is not None else SubprocessGemmaGenerator(model_dir)
        )

    @property
    def model_dir(self) -> Path:
        return self._model_dir

    @classmethod
    def from_data_root(
        cls,
        data_root: Path,
        *,
        generator: GemmaGenerator | None = None,
    ) -> EmbeddedGemmaLLM:
        root = artifact_dir(data_root, EMBEDDED_GEMMA_ID)
        return cls(model_dir=find_model_dir(root), generator=generator)

    def complete(
        self, prompt: str, *, json_schema: dict[str, object] | None = None
    ) -> str:
        del json_schema
        return self._generator.generate(prompt)


def embedded_gemma_installed(data_root: Path) -> bool:
    """Return whether the pinned Gemma 4 E2B snapshot is present and complete."""
    lock = load_models_lock()
    by_id = {artifact.id: artifact for artifact in lock.artifacts}
    artifact = by_id[EMBEDDED_GEMMA_ID]
    marker = artifact_revision_path(data_root, EMBEDDED_GEMMA_ID)
    if not marker.is_file():
        return False
    try:
        installed = marker.read_text(encoding="utf-8").strip()
    except OSError:
        return False
    if installed != artifact.revision:
        return False
    return (artifact_dir(data_root, EMBEDDED_GEMMA_ID) / "config.json").is_file()
