"""LLM abstractions for LexiFlow."""

from lexiflow_core.llm.fake import FakeLLM
from lexiflow_core.llm.protocol import LLMProvider

__all__ = ["FakeLLM", "LLMProvider"]
