"""Serialize and deserialize global settings for TOML storage."""

from __future__ import annotations

from dataclasses import fields
from pathlib import Path
from typing import Any

from lexiflow_core.config.settings import Settings


def settings_to_mapping(settings: Settings) -> dict[str, Any]:
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


def settings_from_mapping(raw: dict[str, Any]) -> Settings:
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
