"""Choose an embedder for the worker process."""

from __future__ import annotations

import logging
from pathlib import Path

from lexiflow_core.embeddings.fake import FakeEmbedder
from lexiflow_core.embeddings.protocol import Embedder
from lexiflow_core.models.paths import artifact_revision_path
from lexiflow_core.models.requirements import EMBEDDING_MINILM_ID

logger = logging.getLogger(__name__)


def resolve_embedder(data_root: Path) -> Embedder:
    """Return MiniLM when installed and loadable, otherwise FakeEmbedder."""
    marker = artifact_revision_path(data_root, EMBEDDING_MINILM_ID)
    if marker.is_file():
        try:
            import importlib

            importlib.import_module("sentence_transformers")
            from lexiflow_core.embeddings.minilm import MiniLMEmbedder
        except Exception as exc:
            logger.warning(
                "MiniLM artifact present but embedder unavailable (%s); "
                "using FakeEmbedder",
                exc,
            )
            return FakeEmbedder()
        logger.info("using MiniLM embedder from %s", marker.parent)
        return MiniLMEmbedder(data_root)
    logger.info("MiniLM not installed; using FakeEmbedder")
    return FakeEmbedder()
