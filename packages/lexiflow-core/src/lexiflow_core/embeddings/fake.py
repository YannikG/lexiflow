"""Deterministic embedder for tests and manual worker runs."""

from __future__ import annotations

import hashlib
import struct

from lexiflow_core.vectors.models import EMBEDDING_DIM


class FakeEmbedder:
    """Return stable 384-dimensional vectors derived from input text."""

    def embed(self, text: str) -> list[float]:
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        values: list[float] = []
        while len(values) < EMBEDDING_DIM:
            for offset in range(0, len(digest), 4):
                if len(values) == EMBEDDING_DIM:
                    break
                chunk = digest[offset : offset + 4]
                if len(chunk) < 4:
                    chunk = chunk.ljust(4, b"\0")
                (raw,) = struct.unpack(">I", chunk)
                values.append((raw / 2**32) * 2.0 - 1.0)
            digest = hashlib.sha256(digest).digest()
        return values
