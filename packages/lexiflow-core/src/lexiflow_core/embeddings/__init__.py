"""Embedding abstractions and test doubles."""

from lexiflow_core.embeddings.fake import FakeEmbedder
from lexiflow_core.embeddings.protocol import Embedder

__all__ = ["Embedder", "FakeEmbedder"]
