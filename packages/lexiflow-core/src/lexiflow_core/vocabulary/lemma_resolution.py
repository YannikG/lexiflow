"""Lemma resolution via spaCy pack or LLM job."""

from __future__ import annotations

from pathlib import Path

from lexiflow_core.vocabulary.lemma_form import normalize_lemma
from lexiflow_core.vocabulary.lemma_output import LemmaInferenceResult
from lexiflow_core.vocabulary.models import WordCategory

_SPACY_POS_TO_CATEGORY: dict[str, WordCategory] = {
    "NOUN": WordCategory.NOUN,
    "VERB": WordCategory.VERB,
    "ADJ": WordCategory.ADJECTIVE,
    "ADV": WordCategory.ADVERB,
    "PRON": WordCategory.PRONOUN,
    "ADP": WordCategory.PREPOSITION,
    "CCONJ": WordCategory.CONJUNCTION,
    "SCONJ": WordCategory.CONJUNCTION,
    "INTJ": WordCategory.INTERJECTION,
}


def spacy_pack_dir(data_root: Path, language_code: str) -> Path:
    """Return the directory where a downloaded spaCy pack is expected."""
    return data_root / ".app" / "spacy" / language_code


def spacy_pack_available(data_root: Path, language_code: str) -> bool:
    """Return whether a spaCy language pack directory exists."""
    pack_dir = spacy_pack_dir(data_root, language_code)
    return pack_dir.is_dir() and any(pack_dir.iterdir())


def resolve_lemma_with_spacy(
    data_root: Path,
    language_code: str,
    surface_form: str,
) -> LemmaInferenceResult | None:
    """Resolve lemma with spaCy when the pack and library are available."""
    if not spacy_pack_available(data_root, language_code):
        return None
    try:
        import spacy  # type: ignore[import-not-found]
    except ImportError:
        return None
    pack_dir = spacy_pack_dir(data_root, language_code)
    try:
        nlp = spacy.load(str(pack_dir))
    except OSError:
        return None
    doc = nlp(surface_form.strip())
    if not doc:
        return None
    token = doc[0]
    category = _SPACY_POS_TO_CATEGORY.get(token.pos_, WordCategory.OTHER)
    lemma = normalize_lemma(
        token.lemma_,
        language_code=language_code,
        category=category,
    )
    if not lemma:
        return None
    return LemmaInferenceResult(
        lemma=lemma,
        translation="",
        explanation="",
        word_category=category,
    )
