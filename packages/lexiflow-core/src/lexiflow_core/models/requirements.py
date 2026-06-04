"""Constants for models.lock artifact IDs used at runtime."""

from __future__ import annotations

from lexiflow_core.config.settings import Settings

NATIVE_EMBEDDING_ID = "native-embedding"
NATIVE_LLM_ID = "native-llm"


def required_artifact_ids(settings: Settings) -> tuple[str, ...]:
    """Return artifact IDs that onboarding would require before completion.

    v1 returns none: LLM and embedding weights load on first use via llama-server.
    Phase 10b may skip native embedding when Ollama embed is active.
    """
    del settings
    return ()
