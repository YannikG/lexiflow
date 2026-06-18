"""Full-text search over the library index."""

from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass
from uuid import UUID

from lexiflow_core.library.index import LibraryIndex


@dataclass(frozen=True)
class SearchHit:
    """One library search result scoped to a text variant."""

    text_id: UUID
    title: str
    variant: str
    snippet: str
    match_offset: int | None = None


def search_texts(index: LibraryIndex, *, lang: str, query: str) -> list[SearchHit]:
    """Search titles and variant bodies for the active target language."""
    trimmed = query.strip()
    if not trimmed:
        return []
    connection = index._connect()  # noqa: SLF001 — search is index-backed
    try:
        hits = _fts_search(connection, lang=lang, query=trimmed)
        from lexiflow_core.library.trash import trashed_text_ids

        trashed = trashed_text_ids(index._data_root)  # noqa: SLF001
        if trashed:
            hits = [hit for hit in hits if hit.text_id not in trashed]
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


def _mark_offset(snippet: str) -> int | None:
    match = re.search(r"<mark>", snippet)
    if match is None:
        return None
    plain = snippet[: match.start()]
    return len(re.sub(r"\.\.\.", "", plain))
