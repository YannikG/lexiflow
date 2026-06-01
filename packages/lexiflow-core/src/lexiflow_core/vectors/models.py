"""Vector storage domain types."""

from __future__ import annotations

from dataclasses import dataclass

EMBEDDING_DIM = 384


@dataclass(frozen=True)
class WordHit:
    lemma: str
    distance: float
