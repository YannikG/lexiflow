"""Language catalog and per-target-language metadata."""

from lexiflow_core.languages.catalog import get_language, list_languages
from lexiflow_core.languages.models import CEFRLevel, LanguageInfo
from lexiflow_core.languages.setup import (
    LanguageSetupError,
    add_target_with_spacy_download,
    complete_language_onboarding,
)
from lexiflow_core.languages.store import LanguageStore

__all__ = [
    "CEFRLevel",
    "LanguageInfo",
    "LanguageSetupError",
    "LanguageStore",
    "add_target_with_spacy_download",
    "complete_language_onboarding",
    "get_language",
    "list_languages",
]
