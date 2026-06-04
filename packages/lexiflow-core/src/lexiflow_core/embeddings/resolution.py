"""Resolve the production embedder from settings and llama-server health."""

from __future__ import annotations

import logging

from lexiflow_core.config.settings import Settings
from lexiflow_core.embeddings.fake import FakeEmbedder
from lexiflow_core.embeddings.llama_server import LlamaServerEmbedder
from lexiflow_core.embeddings.pins import pinned_embedding_hf_model
from lexiflow_core.embeddings.protocol import Embedder
from lexiflow_core.llm.llama_server import llama_server_health

logger = logging.getLogger(__name__)


def resolve_embedder(settings: Settings) -> Embedder:
    """Return llama-server embedder on native path when healthy, else FakeEmbedder."""
    if settings.ollama_url:
        logger.info("Ollama LLM configured; using FakeEmbedder until phase 10b")
        return FakeEmbedder()
    try:
        pinned_embedding_hf_model()
    except RuntimeError as exc:
        logger.warning("%s; using FakeEmbedder", exc)
        return FakeEmbedder()
    base_url = settings.llama_embed_server_url
    if not llama_server_health(base_url):
        logger.info(
            "llama-server embeddings unavailable at %s; using FakeEmbedder",
            base_url,
        )
        return FakeEmbedder()
    logger.info("using llama-server embedder at %s", base_url)
    return LlamaServerEmbedder(
        base_url=base_url,
        model=pinned_embedding_hf_model(),
    )
