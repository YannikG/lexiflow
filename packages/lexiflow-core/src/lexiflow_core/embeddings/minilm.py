"""MiniLM embedding model (manual verification only; not used in CI)."""

from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any

from lexiflow_core.models.paths import artifact_dir
from lexiflow_core.models.requirements import EMBEDDING_MINILM_ID


class MiniLMEmbedder:
    """Embed text with the pinned local MiniLM artifact."""

    def __init__(self, data_root: Path) -> None:
        self._data_root = data_root

    def embed(self, text: str) -> list[float]:
        sentence_transformers = importlib.import_module("sentence_transformers")
        model_cls: Any = sentence_transformers.SentenceTransformer
        model_dir = artifact_dir(self._data_root, EMBEDDING_MINILM_ID)
        model = model_cls(str(model_dir))
        vector = model.encode(text, normalize_embeddings=False)
        return [float(value) for value in vector.tolist()]
