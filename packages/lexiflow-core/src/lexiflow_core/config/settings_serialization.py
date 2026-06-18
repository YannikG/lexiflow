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


def dump_settings_toml(mapping: dict[str, Any]) -> str:
    """Serialize flat settings keys to TOML (stdlib read via tomllib elsewhere)."""
    lines: list[str] = []
    for key, value in mapping.items():
        if isinstance(value, bool):
            rendered = "true" if value else "false"
        elif isinstance(value, int):
            rendered = str(value)
        elif isinstance(value, str):
            escaped = value.replace("\\", "\\\\").replace('"', '\\"')
            rendered = f'"{escaped}"'
        else:
            msg = f"unsupported settings TOML value for {key!r}: {type(value)!r}"
            raise TypeError(msg)
        lines.append(f"{key} = {rendered}")
    return "\n".join(lines) + "\n"
