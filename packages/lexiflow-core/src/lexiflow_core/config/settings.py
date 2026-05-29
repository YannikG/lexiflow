"""Global settings persistence."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, fields
from pathlib import Path
from typing import Any, Literal

import tomli_w

from lexiflow_core.config.paths import app_config_dir

Theme = Literal["system", "light", "dark"]


class SettingsError(Exception):
    """Raised when global settings cannot be read or written."""


@dataclass
class Settings:
    data_root: Path | None = None
    native_language: str | None = None
    onboarding_complete: bool = False
    ollama_url: str | None = None
    llm_enabled: bool = True
    theme: Theme = "system"


class SettingsStore:
    def __init__(self, config_dir: Path | None = None) -> None:
        self._config_dir = config_dir if config_dir is not None else app_config_dir()

    @property
    def settings_path(self) -> Path:
        return self._config_dir / "settings.toml"

    def load(self) -> Settings:
        if not self.settings_path.is_file():
            return Settings()
        try:
            with self.settings_path.open("rb") as handle:
                raw = tomllib.load(handle)
        except tomllib.TOMLDecodeError as exc:
            raise SettingsError("invalid settings.toml") from exc
        return _settings_from_mapping(raw)

    def save(self, settings: Settings) -> None:
        self._config_dir.mkdir(parents=True, exist_ok=True)
        payload = _settings_to_mapping(settings)
        with self.settings_path.open("wb") as handle:
            tomli_w.dump(payload, handle)


def _settings_to_mapping(settings: Settings) -> dict[str, Any]:
    mapping: dict[str, Any] = {}
    for field in fields(settings):
        value = getattr(settings, field.name)
        if value is None:
            continue
        if isinstance(value, Path):
            mapping[field.name] = str(value)
        else:
            mapping[field.name] = value
    return mapping


def _settings_from_mapping(raw: dict[str, Any]) -> Settings:
    kwargs: dict[str, Any] = {}
    valid_names = {field.name for field in fields(Settings)}
    for key, value in raw.items():
        if key not in valid_names:
            continue
        if key == "data_root" and value is not None:
            kwargs[key] = Path(str(value))
        else:
            kwargs[key] = value
    return Settings(**kwargs)
