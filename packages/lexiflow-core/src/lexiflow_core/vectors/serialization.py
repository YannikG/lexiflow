"""Serialize embedding vectors for sqlite-vec storage."""

from __future__ import annotations

import json
import struct

from lexiflow_core.vectors.models import EMBEDDING_DIM


def serialize_float32(vector: list[float]) -> bytes:
    """Pack a float vector into sqlite-vec compact binary format."""
    if len(vector) != EMBEDDING_DIM:
        msg = f"expected {EMBEDDING_DIM} dimensions, got {len(vector)}"
        raise ValueError(msg)
    return struct.pack(f"{EMBEDDING_DIM}f", *vector)


def deserialize_float32(blob: bytes) -> list[float]:
    """Unpack a compact binary vector from sqlite-vec."""
    return list(struct.unpack(f"{EMBEDDING_DIM}f", blob))


def vector_from_json(json_text: str) -> list[float]:
    """Parse a sqlite-vec JSON vector representation."""
    values = json.loads(json_text)
    if not isinstance(values, list):
        raise ValueError("expected JSON array")
    return [float(value) for value in values]
