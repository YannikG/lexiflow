"""Pinned embedding model helpers from models.lock."""

from __future__ import annotations

from lexiflow_core.models.lockfile import ModelArtifact, load_models_lock
from lexiflow_core.models.requirements import NATIVE_EMBEDDING_ID


def pinned_embedding_artifact() -> ModelArtifact:
    """Return the pinned native embedding artifact from models.lock."""
    lock = load_models_lock()
    by_id = {artifact.id: artifact for artifact in lock.artifacts}
    artifact = by_id.get(NATIVE_EMBEDDING_ID)
    if artifact is None:
        raise RuntimeError(f"{NATIVE_EMBEDDING_ID} is missing from models.lock")
    return artifact


def pinned_embedding_hf_model() -> str:
    """Return the Hugging Face model spec passed to llama-server ``-hf``."""
    artifact = pinned_embedding_artifact()
    if artifact.llama_hf_model:
        return artifact.llama_hf_model
    raise RuntimeError(
        f"{NATIVE_EMBEDDING_ID} is missing llama_hf_model in models.lock"
    )
