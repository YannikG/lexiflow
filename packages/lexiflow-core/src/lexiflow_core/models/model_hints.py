"""Human-readable model names for onboarding UI."""

from __future__ import annotations

from lexiflow_core.models.lockfile import ModelsLock, load_models_lock
from lexiflow_core.models.requirements import EMBEDDED_GEMMA_ID, EMBEDDING_MINILM_ID


def artifact_hint(artifact_id: str, lock: ModelsLock | None = None) -> str:
    """Return helper text describing which Hub model folder to import."""
    manifest = lock if lock is not None else load_models_lock()
    by_id = {artifact.id: artifact for artifact in manifest.artifacts}
    artifact = by_id[artifact_id]
    return f"{artifact.repo} (pinned revision {artifact.revision[:12]}…)"


def embedding_import_hint(lock: ModelsLock | None = None) -> str:
    return (
        "Embedding model folder: "
        + artifact_hint(EMBEDDING_MINILM_ID, lock)
        + ". Select the root folder of the downloaded Hugging Face snapshot."
    )


def artifact_hub_page_url(artifact_id: str, lock: ModelsLock | None = None) -> str:
    """Return the Hugging Face model page URL for an artifact."""
    manifest = lock if lock is not None else load_models_lock()
    by_id = {artifact.id: artifact for artifact in manifest.artifacts}
    return f"https://huggingface.co/{by_id[artifact_id].repo}"


def gemma_hub_page_url(lock: ModelsLock | None = None) -> str:
    return artifact_hub_page_url(EMBEDDED_GEMMA_ID, lock)


def gemma_import_hint(lock: ModelsLock | None = None) -> str:
    return (
        "LLM model folder: "
        + artifact_hint(EMBEDDED_GEMMA_ID, lock)
        + ". Accept the Gemma license at "
        + gemma_hub_page_url(lock)
        + " before downloading."
    )
