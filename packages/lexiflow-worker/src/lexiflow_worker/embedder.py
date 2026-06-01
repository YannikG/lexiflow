"""Choose an embedder for the worker process."""

from __future__ import annotations

import importlib
import logging

from lexiflow_core.config.settings import Settings
from lexiflow_core.embeddings.fake import FakeEmbedder
from lexiflow_core.embeddings.minilm import MiniLMEmbedder, pinned_embedding_artifact
from lexiflow_core.embeddings.protocol import Embedder

logger = logging.getLogger(__name__)


def resolve_embedder(settings: Settings) -> Embedder:
    """Return MiniLM when loadable, otherwise FakeEmbedder."""
    try:
        pinned_embedding_artifact()
    except RuntimeError as exc:
        logger.warning("%s; using FakeEmbedder", exc)
        return FakeEmbedder()
    try:
        importlib.import_module("sentence_transformers")
    except Exception as exc:
        logger.info(
            "sentence-transformers unavailable (%s); using FakeEmbedder",
            exc,
        )
        return FakeEmbedder()
    logger.info("using MiniLM embedder from Hugging Face pin")
    return MiniLMEmbedder(token=settings.huggingface_token)
