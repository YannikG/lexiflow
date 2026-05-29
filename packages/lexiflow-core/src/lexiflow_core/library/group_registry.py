"""Load and save the per-language group display-name registry."""

from __future__ import annotations

import json
from pathlib import Path

from lexiflow_core.config.paths import groups_json_path
from lexiflow_core.library.group_names import slugify_group_name


class GroupRegistryError(Exception):
    """Raised when the group registry cannot be read or written."""


class GroupNotFoundError(GroupRegistryError):
    """Raised when a group display name or folder slug is unknown."""


class GroupSlugCollisionError(GroupRegistryError):
    """Raised when a group folder slug is already used by another display name."""


class GroupRegistry:
    def __init__(self, data_root: Path, language_code: str) -> None:
        self._path = groups_json_path(data_root, language_code)

    def load(self) -> dict[str, str]:
        """Return folder_slug → display_name mapping."""
        if not self._path.is_file():
            return {}
        try:
            raw = json.loads(self._path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise GroupRegistryError(f"failed to read {self._path}") from exc
        if not isinstance(raw, dict):
            raise GroupRegistryError(f"invalid group registry format in {self._path}")
        return {str(key): str(value) for key, value in raw.items()}

    def save(self, mapping: dict[str, str]) -> None:
        """Persist folder_slug → display_name mapping."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        try:
            self._path.write_text(
                json.dumps(mapping, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
        except OSError as exc:
            raise GroupRegistryError(f"failed to write {self._path}") from exc

    def register(self, display_name: str) -> str:
        """Add a group and return its folder slug."""
        folder_slug = slugify_group_name(display_name)
        mapping = self.load()
        for slug, name in mapping.items():
            if name == display_name:
                return slug
        existing = mapping.get(folder_slug)
        if existing is not None and existing != display_name:
            raise GroupSlugCollisionError(
                f"group folder slug {folder_slug!r} is already used by {existing!r}"
            )
        mapping[folder_slug] = display_name
        self.save(mapping)
        return folder_slug

    def folder_slug_for_display(self, display_name: str) -> str:
        """Resolve a display name to its folder slug."""
        mapping = self.load()
        for slug, name in mapping.items():
            if name == display_name:
                return slug
        raise GroupNotFoundError(f"group not found: {display_name!r}")

    def display_name_for_folder(self, folder_slug: str) -> str:
        """Resolve a folder slug to its display name."""
        mapping = self.load()
        if folder_slug not in mapping:
            raise GroupNotFoundError(f"group folder not found: {folder_slug!r}")
        return mapping[folder_slug]

    def remove(self, folder_slug: str) -> None:
        """Remove a group entry from the registry."""
        mapping = self.load()
        if folder_slug not in mapping:
            raise GroupNotFoundError(f"group folder not found: {folder_slug!r}")
        del mapping[folder_slug]
        self.save(mapping)

    def rename(self, old_display: str, new_display: str) -> tuple[str, str]:
        """Rename a group's display label and return old and new folder slugs."""
        old_slug = self.folder_slug_for_display(old_display)
        new_slug = slugify_group_name(new_display)
        mapping = self.load()
        existing = mapping.get(new_slug)
        if existing is not None and existing != old_display:
            raise GroupSlugCollisionError(
                f"group folder slug {new_slug!r} is already used by {existing!r}"
            )
        del mapping[old_slug]
        mapping[new_slug] = new_display
        self.save(mapping)
        return old_slug, new_slug

    def list_display_names(self) -> list[str]:
        """Return all registered group display names."""
        mapping = self.load()
        return sorted(mapping.values(), key=str.casefold)

    def ensure_for_folder(self, folder_slug: str, display_name: str) -> None:
        """Register a folder slug if missing (used during rebuild)."""
        mapping = self.load()
        if folder_slug not in mapping:
            mapping[folder_slug] = display_name
            self.save(mapping)
