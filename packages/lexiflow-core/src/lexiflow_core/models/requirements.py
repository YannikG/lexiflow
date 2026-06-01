"""Policy for which model artifacts onboarding must install."""

from __future__ import annotations

from lexiflow_core.config.settings import Settings

EMBEDDING_MINILM_ID = "embedding-minilm"
NATIVE_LLM_ID = "native-llm"

# Backward-compatible alias for tests and docs migrating off embedded-gemma.
EMBEDDED_GEMMA_ID = NATIVE_LLM_ID


def required_artifact_ids(settings: Settings) -> tuple[str, ...]:
    """Return artifact IDs LexiFlow must download before onboarding completes."""
    del settings
    return ()
