"""Reader tab identifiers and simplified variant discovery."""

from __future__ import annotations

from pathlib import Path

from lexiflow_core.config.paths import variant_path

DEFAULT_TAB = "translated"
NATIVE_TAB = "native"
TRANSLATED_TAB = "translated"
SIMPLIFIED_PREFIX = "simplified-"


def discover_simplified_variants(text_folder: Path) -> tuple[str, ...]:
    """Return simplified variant names present on disk, sorted by level label."""
    names: list[str] = []
    for path in sorted(text_folder.glob("simplified-*.md")):
        stem = path.stem
        if variant_path(text_folder, stem).is_file():
            names.append(stem)
    return tuple(names)


def simplified_tab_label(variant_name: str) -> str:
    """Return a user-facing level label for a simplified variant filename stem."""
    if not variant_name.startswith(SIMPLIFIED_PREFIX):
        return variant_name
    return variant_name.removeprefix(SIMPLIFIED_PREFIX).upper()


def resolve_open_tab(
    last_viewed: str | None,
    *,
    available_variants: tuple[str, ...],
    simplified_variants: tuple[str, ...],
) -> str:
    """Pick the reader tab to show when opening a text."""
    if last_viewed is None:
        return DEFAULT_TAB
    if last_viewed == NATIVE_TAB and NATIVE_TAB in available_variants:
        return NATIVE_TAB
    if last_viewed == TRANSLATED_TAB and TRANSLATED_TAB in available_variants:
        return TRANSLATED_TAB
    if last_viewed in simplified_variants:
        return last_viewed
    return DEFAULT_TAB
