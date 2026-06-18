"""Orchestrates add-text validation, text creation, and staged job enqueue."""

from __future__ import annotations

from pathlib import Path
from uuid import UUID

from lexiflow_core.jobs.handlers.cleanup import SOURCE_ROUTE_NATIVE, SOURCE_ROUTE_TARGET
from lexiflow_core.jobs.models import JobRequest, JobType
from lexiflow_core.jobs.service import JobService
from lexiflow_core.library.document_title import resolve_create_title
from lexiflow_core.library.index import LibraryIndex
from lexiflow_core.library.models import CreateTextRequest
from lexiflow_core.library.text_repository import TextRepository
from lexiflow_core.text_pipeline.models import TextDraft
from lexiflow_core.text_pipeline.routing import resolve_source_route
from lexiflow_core.text_pipeline.types import TextId

LARGE_PASTE_THRESHOLD = 50_000


class DuplicateWarning(Exception):
    """Raised when pasted content or URL matches an existing text."""

    def __init__(self, existing_id: UUID) -> None:
        self.existing_id = existing_id
        super().__init__(f"duplicate text: {existing_id}")


class LargePasteRequiresConfirmation(Exception):
    """Raised when pasted content exceeds the soft size guard without confirmation."""


def _find_duplicate_by_url(
    index: LibraryIndex,
    *,
    target_language: str,
    source_url: str | None,
) -> UUID | None:
    normalized_url = source_url.strip() if source_url is not None else None
    if not normalized_url:
        return None
    return index.find_by_source_url(target_language, normalized_url)


class TextPipeline:
    def __init__(
        self,
        data_root: Path,
        *,
        index: LibraryIndex | None = None,
        job_service: JobService | None = None,
        text_repository: TextRepository | None = None,
    ) -> None:
        self._data_root = data_root
        self._index = index if index is not None else LibraryIndex(data_root)
        self._jobs = job_service if job_service is not None else JobService(data_root)
        self._texts = (
            text_repository
            if text_repository is not None
            else TextRepository(data_root, self._index)
        )

    def submit_new_text(self, draft: TextDraft) -> TextId:
        """Validate draft, create provisional text, and enqueue staged generation."""
        is_large = len(draft.pasted_content) > LARGE_PASTE_THRESHOLD
        if is_large and not draft.confirmed_large_paste:
            raise LargePasteRequiresConfirmation()

        if not draft.ignore_duplicate:
            existing = _find_duplicate_by_url(
                self._index,
                target_language=draft.target_language,
                source_url=draft.source_url,
            )
            if existing is not None:
                raise DuplicateWarning(existing)

        source_route = resolve_source_route(
            input_tab=draft.input_tab,
            detected_language=None,
            native_language=draft.native_language,
            target_language=draft.target_language,
        )
        route_value = (
            SOURCE_ROUTE_NATIVE if source_route == "native" else SOURCE_ROUTE_TARGET
        )

        create_title, autogenerate_title = resolve_create_title(draft.title)
        record = self._texts.create_text(
            CreateTextRequest(
                title=create_title,
                group=draft.group,
                target_language=draft.target_language,
                native_language=draft.native_language,
                body=draft.pasted_content,
                source_url=draft.source_url,
                autogenerate_title=autogenerate_title,
            )
        )
        self._jobs.enqueue(
            JobRequest(
                job_type=JobType.CLEANUP,
                payload={
                    "text_id": str(record.id),
                    "raw_paste": draft.pasted_content,
                    "source_route": route_value,
                },
            )
        )
        return record.id
