"""Constants for models.lock artifact IDs used at runtime."""

from __future__ import annotations

from lexiflow_core.config.settings import Settings

EMBEDDING_MINILM_ID = "embedding-minilm"
NATIVE_LLM_ID = "native-llm"


def required_artifact_ids(settings: Settings) -> tuple[str, ...]:
    """Return artifact IDs that onboarding would require before completion.

    v1 returns none: LLM and embedding weights load on first use via llama-server
    and sentence-transformers. Phase 10b may skip MiniLM when Ollama embed is active.
    """
    del settings
    return ()
