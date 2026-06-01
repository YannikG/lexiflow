"""Domain types for languages and proficiency levels."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class CEFRLevel(StrEnum):
    A1 = "A1"
    A2 = "A2"
    B1 = "B1"
    B2 = "B2"
    C1 = "C1"
    C2 = "C2"


_CEFR_ORDER: tuple[CEFRLevel, ...] = (
    CEFRLevel.A1,
    CEFRLevel.A2,
    CEFRLevel.B1,
    CEFRLevel.B2,
    CEFRLevel.C1,
    CEFRLevel.C2,
)


def level_below(level: CEFRLevel) -> CEFRLevel | None:
    """Return one CEFR level below ``level``, or None at A1."""
    index = _CEFR_ORDER.index(level)
    if index == 0:
        return None
    return _CEFR_ORDER[index - 1]


def level_above(level: CEFRLevel) -> CEFRLevel | None:
    """Return one CEFR level above ``level``, or None at C2."""
    index = _CEFR_ORDER.index(level)
    if index >= len(_CEFR_ORDER) - 1:
        return None
    return _CEFR_ORDER[index + 1]


@dataclass(frozen=True)
class LanguageInfo:
    iso: str
    name: str
    flag: str
