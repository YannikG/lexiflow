"""Input models for add-text submission."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class InputTab(StrEnum):
    NATIVE = "native"
    TARGET = "target"


@dataclass(frozen=True)
class TextDraft:
    group: str
    pasted_content: str
    input_tab: InputTab
    native_language: str
    target_language: str
    source_url: str | None = None
    ignore_duplicate: bool = False
    confirmed_large_paste: bool = False
