"""Simplify job handler."""

from __future__ import annotations

from pathlib import Path
from uuid import UUID

from lexiflow_core.jobs.models import JobRecord
from lexiflow_core.jobs.service import JobService
from lexiflow_core.languages.models import CEFRLevel
from lexiflow_core.library.document_title import format_document_title
from lexiflow_core.library.reader_tabs import simplified_variant_name
from lexiflow_core.library.text_repository import TextRepository
from lexiflow_core.llm.prompt_languages import prompt_language_label
from lexiflow_core.llm.prompts import render_prompt
from lexiflow_core.llm.protocol import LLMProvider
from lexiflow_core.simplify.new_words import filter_suggestions
from lexiflow_core.simplify.structured_output import (
    SimplifyOutputError,
    parse_simplify_output,
    simplify_json_schema,
)
from lexiflow_core.simplify.suggestions_store import save_suggestions
from lexiflow_core.simplify.word_mix import (
    VocabWordForMix,
    rank_words,
    select_prompt_words,
)
from lexiflow_core.vectors.models import WordHit
from lexiflow_core.vectors.setup import ensure_vocabulary_db
from lexiflow_core.vectors.store import VectorStore
from lexiflow_core.vocabulary.models import VocabularyEntry
from lexiflow_core.vocabulary.store import VocabularyStore


def _text_id_from_payload(job: JobRecord) -> UUID:
    raw = job.payload.get("text_id")
    if not isinstance(raw, str):
        raise ValueError(f"job {job.id} is missing text_id")
    return UUID(raw)


def _level_from_payload(job: JobRecord) -> CEFRLevel:
    raw = job.payload.get("level")
    if not isinstance(raw, str):
        raise ValueError(f"job {job.id} is missing level")
    try:
        return CEFRLevel(raw.strip().upper())
    except ValueError as exc:
        raise ValueError(f"job {job.id} has invalid level: {raw!r}") from exc


def _build_word_mix(
    *,
    data_root: Path,
    target_language: str,
    text_id: UUID,
    target_level: CEFRLevel,
    vector_store: VectorStore | None = None,
    vocabulary_store: VocabularyStore | None = None,
) -> list[str]:
    store = (
        vector_store
        if vector_store is not None
        else VectorStore(data_root, target_language)
    )
    vocab = (
        vocabulary_store
        if vocabulary_store is not None
        else VocabularyStore(data_root, target_language)
    )
    entries = {entry.lemma: entry for entry in vocab.list_for_simplify()}
    if not entries:
        return []
    text_vector = store.get_text_vector(text_id)
    if text_vector is None:
        return []
    hits = store.search_similar_words(text_vector, limit=100)
    words_for_mix = _hits_to_mix_words(hits, entries)
    ranked = rank_words(words_for_mix)
    return select_prompt_words(ranked, target_level)


def _hits_to_mix_words(
    hits: list[WordHit],
    entries: dict[str, VocabularyEntry],
) -> list[VocabWordForMix]:
    words: list[VocabWordForMix] = []
    for hit in hits:
        entry = entries.get(hit.lemma)
        if entry is None:
            continue
        words.append(
            VocabWordForMix(
                lemma=entry.lemma,
                level=entry.level_when_learned,
                difficulty=entry.difficulty_rating,
                distance=hit.distance,
            )
        )
    return words


def _format_vocabulary_words(words: list[str]) -> str:
    if not words:
        return "(none available)"
    return ", ".join(words)


def handle_simplify(
    job: JobRecord,
    *,
    data_root: Path,
    llm: LLMProvider,
    repo: TextRepository,
    job_service: JobService,
    vector_store: VectorStore | None = None,
    vocabulary_store: VocabularyStore | None = None,
) -> None:
    """Run simplify and persist the simplified variant plus new word suggestions."""
    try:
        text_id = _text_id_from_payload(job)
        target_level = _level_from_payload(job)
    except ValueError as exc:
        job_service.fail(job.id, str(exc))
        return

    record = repo.get_text(text_id)
    folder = Path(record.folder)
    variant_name = simplified_variant_name(target_level)
    ensure_vocabulary_db(data_root, record.target_language)

    try:
        source_markdown = repo.read_variant(text_id, "translated")
    except FileNotFoundError:
        job_service.fail(job.id, f"text {text_id} has no translated variant")
        return

    prompt_words = _build_word_mix(
        data_root=data_root,
        target_language=record.target_language,
        text_id=text_id,
        target_level=target_level,
        vector_store=vector_store,
        vocabulary_store=vocabulary_store,
    )
    prompt = render_prompt(
        "simplify",
        target_level=target_level.value,
        native_language=record.native_language,
        native_language_label=prompt_language_label(record.native_language),
        target_language=record.target_language,
        target_language_label=prompt_language_label(record.target_language),
        vocabulary_words=_format_vocabulary_words(prompt_words),
        source_markdown=source_markdown,
    )
    try:
        raw_output = llm.complete(prompt, json_schema=simplify_json_schema())
        parsed = parse_simplify_output(
            raw_output,
            language_code=record.target_language,
        )
    except SimplifyOutputError as exc:
        job_service.fail(job.id, str(exc))
        return
    except Exception as exc:
        job_service.fail(job.id, str(exc))
        return

    markdown = format_document_title(parsed.title) + parsed.body
    repo.apply_simplified_variant(
        text_id,
        level=target_level.value,
        markdown=markdown,
    )

    vocab = (
        vocabulary_store
        if vocabulary_store is not None
        else VocabularyStore(data_root, record.target_language)
    )
    existing = {entry.lemma for entry in vocab.list_for_simplify()}
    filtered = filter_suggestions(
        parsed.new_words,
        existing_lemmas=existing,
        language_code=record.target_language,
    )
    save_suggestions(folder, variant_name, filtered)
    job_service.complete(job.id, {"variant": variant_name, "level": target_level.value})
