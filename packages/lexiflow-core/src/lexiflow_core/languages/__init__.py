"""Language catalog and per-target-language metadata."""

from lexiflow_core.languages.catalog import get_language, list_languages
from lexiflow_core.languages.models import CEFRLevel, LanguageInfo
from lexiflow_core.languages.setup import add_target_with_spacy_download
from lexiflow_core.languages.store import LanguageStore

__all__ = [
    "CEFRLevel",
    "LanguageInfo",
    "LanguageStore",
    "add_target_with_spacy_download",
    "get_language",
    "list_languages",
]
