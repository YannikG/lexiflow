"""Global settings data model."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

Theme = Literal["system", "light", "dark"]


class SettingsError(Exception):
    """Raised when global settings cannot be read or written."""


@dataclass
class Settings:
    data_root: Path | None = None
    native_language: str | None = None
    active_target_language: str | None = None
    onboarding_complete: bool = False
    ollama_url: str | None = None
    llama_server_url: str = "http://127.0.0.1:8080"
    llama_embed_server_url: str = "http://127.0.0.1:8081"
    huggingface_token: str | None = None
    theme: Theme = "system"
    reader_font_size: int = 14
