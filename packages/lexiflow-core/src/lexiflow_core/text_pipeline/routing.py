"""Input tab and language auto-detect routing."""

from __future__ import annotations

from typing import Literal

from lexiflow_core.text_pipeline.models import InputTab

SourceRoute = Literal["native", "target"]


def resolve_source_route(
    *,
    input_tab: InputTab,
    detected_language: str | None,
    native_language: str,
    target_language: str,
) -> SourceRoute:
    """Resolve source route; language detect overrides tab when they conflict."""
    tab_expects_native = input_tab == InputTab.NATIVE
    if detected_language is None:
        return "native" if tab_expects_native else "target"

    detected_is_native = detected_language == native_language
    detected_is_target = detected_language == target_language

    if detected_is_native:
        return "native"
    if detected_is_target:
        return "target"
    return "native" if tab_expects_native else "target"
