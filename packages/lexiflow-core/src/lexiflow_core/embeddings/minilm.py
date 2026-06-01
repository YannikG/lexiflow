"""MiniLM embedding model (manual verification only; not used in CI)."""

from __future__ import annotations

import importlib
from typing import Any

from lexiflow_core.models.lockfile import ModelArtifact, load_models_lock
from lexiflow_core.models.requirements import EMBEDDING_MINILM_ID


def pinned_embedding_artifact() -> ModelArtifact:
    """Return the pinned embedding artifact from models.lock."""
    lock = load_models_lock()
    by_id = {artifact.id: artifact for artifact in lock.artifacts}
    artifact = by_id.get(EMBEDDING_MINILM_ID)
    if artifact is None:
        raise RuntimeError(f"{EMBEDDING_MINILM_ID} is missing from models.lock")
    return artifact


class MiniLMEmbedder:
    """Embed text with the pinned Hugging Face MiniLM model."""

    def __init__(self, *, token: str | None = None) -> None:
        self._token = token
        self._model: Any | None = None

    def embed(self, text: str) -> list[float]:
        if self._model is None:
            artifact = pinned_embedding_artifact()
            sentence_transformers = importlib.import_module("sentence_transformers")
            model_cls: Any = sentence_transformers.SentenceTransformer
            self._model = model_cls(
                artifact.repo,
                revision=artifact.revision,
                token=self._token,
            )
        vector = self._model.encode(text, normalize_embeddings=False)
        return [float(value) for value in vector.tolist()]
