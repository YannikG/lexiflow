"""Persist global settings to settings.toml."""

from __future__ import annotations

import tomllib
from pathlib import Path

import tomli_w

from lexiflow_core.config.platform_dirs import app_config_dir
from lexiflow_core.config.settings import Settings, SettingsError
from lexiflow_core.config.settings_serialization import (
    settings_from_mapping,
    settings_to_mapping,
)


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
        except OSError as exc:
            raise SettingsError("failed to read settings.toml") from exc
        return settings_from_mapping(raw)

    def save(self, settings: Settings) -> None:
        try:
            self._config_dir.mkdir(parents=True, exist_ok=True)
            with self.settings_path.open("wb") as handle:
                tomli_w.dump(settings_to_mapping(settings), handle)
        except OSError as exc:
            raise SettingsError("failed to save settings") from exc
