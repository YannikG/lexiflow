"""Human-readable model names for onboarding UI."""

from __future__ import annotations

from lexiflow_core.models.lockfile import ModelsLock, load_models_lock
from lexiflow_core.models.requirements import EMBEDDING_MINILM_ID, NATIVE_LLM_ID


def artifact_hint(artifact_id: str, lock: ModelsLock | None = None) -> str:
    """Return helper text describing a pinned Hugging Face model."""
    manifest = lock if lock is not None else load_models_lock()
    by_id = {artifact.id: artifact for artifact in manifest.artifacts}
    artifact = by_id[artifact_id]
    return f"{artifact.repo} (pinned revision {artifact.revision[:12]}…)"


def artifact_hub_page_url(artifact_id: str, lock: ModelsLock | None = None) -> str:
    """Return the Hugging Face model page URL for an artifact."""
    manifest = lock if lock is not None else load_models_lock()
    by_id = {artifact.id: artifact for artifact in manifest.artifacts}
    return f"https://huggingface.co/{by_id[artifact_id].repo}"


def native_llm_hub_page_url(lock: ModelsLock | None = None) -> str:
    return artifact_hub_page_url(NATIVE_LLM_ID, lock)


def embedding_hub_page_url(lock: ModelsLock | None = None) -> str:
    return artifact_hub_page_url(EMBEDDING_MINILM_ID, lock)
