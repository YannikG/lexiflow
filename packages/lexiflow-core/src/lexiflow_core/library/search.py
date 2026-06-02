"""Full-text search over the library index."""

from __future__ import annotations

import re
import sqlite3
from uuid import UUID

from rapidfuzz import fuzz

from lexiflow_core.library.index import LibraryIndex
from lexiflow_core.library.search_models import SearchHit

_FUZZY_SCORE_CUTOFF = 70
_SNIPPET_RADIUS = 40


def search_texts(index: LibraryIndex, *, lang: str, query: str) -> list[SearchHit]:
    """Search titles and variant bodies for the active target language."""
    trimmed = query.strip()
    if not trimmed:
        return []
    connection = index._connect()  # noqa: SLF001 — search is index-backed
    try:
        hits = _fts_search(connection, lang=lang, query=trimmed)
        if not hits:
            hits = _fuzzy_search(connection, lang=lang, query=trimmed)
        return hits
    finally:
        connection.close()


def _fts_search(
    connection: sqlite3.Connection, *, lang: str, query: str
) -> list[SearchHit]:
    fts_query = _fts_prefix_query(query)
    if not fts_query:
        return []
    rows = connection.execute(
        """
        SELECT text_id, variant, title,
               snippet(text_search, 4, '<mark>', '</mark>', '...', 32)
        FROM text_search
        WHERE lang = ? AND text_search MATCH ?
        ORDER BY rank
        """,
        (lang, fts_query),
    ).fetchall()
    return [_hit_from_fts_row(row) for row in rows]


def _fuzzy_search(
    connection: sqlite3.Connection, *, lang: str, query: str
) -> list[SearchHit]:
    rows = connection.execute(
        """
        SELECT text_id, variant, title, body
        FROM text_search
        WHERE lang = ?
        """,
        (lang,),
    ).fetchall()
    query_lower = query.lower()
    hits: list[SearchHit] = []
    seen: set[tuple[str, str]] = set()
    for text_id, variant, title, body in rows:
        key = (str(text_id), str(variant))
        if key in seen:
            continue
        title_text = str(title)
        body_text = str(body)
        match = _best_fuzzy_match(query_lower, title_text, body_text)
        if match is None:
            continue
        field_text, offset = match
        seen.add(key)
        hits.append(
            SearchHit(
                text_id=UUID(str(text_id)),
                title=title_text,
                variant=str(variant),
                snippet=_snippet_with_mark(field_text, offset, len(query)),
                match_offset=offset if field_text is body_text else None,
            )
        )
    hits.sort(key=lambda hit: hit.title.casefold())
    return hits


def _hit_from_fts_row(row: sqlite3.Row | tuple[object, ...]) -> SearchHit:
    text_id, variant, title, snippet = row
    snippet_text = str(snippet)
    match_offset = _mark_offset(snippet_text)
    return SearchHit(
        text_id=UUID(str(text_id)),
        title=str(title),
        variant=str(variant),
        snippet=snippet_text,
        match_offset=match_offset,
    )


def _fts_prefix_query(query: str) -> str:
    terms = query.split()
    if not terms:
        return ""
    parts: list[str] = []
    for term in terms:
        escaped = term.replace('"', '""')
        parts.append(f'"{escaped}"*')
    return " AND ".join(parts)


def _best_fuzzy_match(
    query_lower: str, title: str, body: str
) -> tuple[str, int] | None:
    best: tuple[str, int, float] | None = None
    for field in (title, body):
        field_lower = field.lower()
        score = fuzz.partial_ratio(
            query_lower, field_lower, score_cutoff=_FUZZY_SCORE_CUTOFF
        )
        if score == 0:
            continue
        offset = _fuzzy_match_offset(query_lower, field_lower)
        if best is None or score > best[2]:
            best = (field, offset, score)
    if best is None:
        return None
    return best[0], best[1]


def _fuzzy_match_offset(query_lower: str, field_lower: str) -> int:
    if query_lower in field_lower:
        return field_lower.index(query_lower)
    alignment = fuzz.partial_ratio_alignment(query_lower, field_lower)
    if alignment is None:
        return 0
    return alignment.dest_start


def _snippet_with_mark(text: str, offset: int, match_len: int) -> str:
    start = max(0, offset - _SNIPPET_RADIUS)
    end = min(len(text), offset + match_len + _SNIPPET_RADIUS)
    prefix = "..." if start > 0 else ""
    suffix = "..." if end < len(text) else ""
    matched = text[offset : offset + match_len]
    before = text[start:offset]
    after = text[offset + match_len : end]
    return f"{prefix}{before}<mark>{matched}</mark>{after}{suffix}"


def _mark_offset(snippet: str) -> int | None:
    match = re.search(r"<mark>", snippet)
    if match is None:
        return None
    plain = snippet[: match.start()]
    return len(re.sub(r"\.\.\.", "", plain))
