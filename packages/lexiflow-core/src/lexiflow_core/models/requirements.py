"""Policy for which model artifacts onboarding must install."""

from __future__ import annotations

from lexiflow_core.config.settings import Settings

EMBEDDING_MINILM_ID = "embedding-minilm"
EMBEDDED_GEMMA_ID = "embedded-gemma"


def required_artifact_ids(settings: Settings) -> tuple[str, ...]:
    """Return artifact IDs required before onboarding can complete."""
    if settings.ollama_url:
        return (EMBEDDING_MINILM_ID,)
    return (EMBEDDING_MINILM_ID, EMBEDDED_GEMMA_ID)
