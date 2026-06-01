"""Reader tab identifiers and simplified variant discovery."""

from __future__ import annotations

from pathlib import Path

from lexiflow_core.config.paths import variant_path
from lexiflow_core.languages.models import CEFRLevel

DEFAULT_TAB = "translated"
NATIVE_TAB = "native"
TRANSLATED_TAB = "translated"
SIMPLIFIED_PREFIX = "simplified-"


def simplified_variant_name(level: CEFRLevel) -> str:
    """Return on-disk variant stem for a simplified level (e.g. ``simplified-a2``)."""
    return f"{SIMPLIFIED_PREFIX}{level.value.lower()}"


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


def level_from_simplified_variant(variant_name: str) -> CEFRLevel | None:
    """Parse the CEFR level encoded in a simplified variant stem."""
    if not variant_name.startswith(SIMPLIFIED_PREFIX):
        return None
    try:
        return CEFRLevel(simplified_tab_label(variant_name))
    except ValueError:
        return None


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
