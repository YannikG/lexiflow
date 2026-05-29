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


@dataclass(frozen=True)
class LanguageInfo:
    iso: str
    name: str
    flag: str
