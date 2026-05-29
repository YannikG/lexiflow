"""Language detection protocol for add-text routing."""

from __future__ import annotations

from typing import Protocol


class LanguageDetector(Protocol):
    def detect(self, text: str) -> str | None:
        """Return an ISO language code for the text, or None when unknown."""


class FakeLanguageDetector:
    """Test double with a fixed detection result."""

    def __init__(self, *, detected: str | None) -> None:
        self._detected = detected

    def detect(self, text: str) -> str | None:
        del text
        return self._detected


class LangdetectLanguageDetector:
    """Detect paste language via langdetect (ISO 639-1 codes)."""

    def __init__(self, *, min_chars: int = 40) -> None:
        self._min_chars = min_chars

    def detect(self, text: str) -> str | None:
        sample = text.strip()
        if len(sample) < self._min_chars:
            return None
        try:
            from langdetect import detect
            from langdetect.lang_detect_exception import LangDetectException
        except ImportError:
            return None
        try:
            code = detect(sample)
        except LangDetectException:
            return None
        if not isinstance(code, str):
            return None
        return code.split("-", maxsplit=1)[0].lower()
