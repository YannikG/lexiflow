"""Orchestrates add-text validation, text creation, and staged job enqueue."""

from __future__ import annotations

from pathlib import Path
from uuid import UUID

from lexiflow_core.jobs.handlers.cleanup import SOURCE_ROUTE_NATIVE, SOURCE_ROUTE_TARGET
from lexiflow_core.jobs.models import JobRequest, JobType
from lexiflow_core.jobs.service import JobService
from lexiflow_core.library.index import LibraryIndex
from lexiflow_core.library.models import CreateTextRequest
from lexiflow_core.library.text_repository import TextRepository
from lexiflow_core.text_pipeline.duplicate_checker import DuplicateChecker
from lexiflow_core.text_pipeline.language_detect import LanguageDetector
from lexiflow_core.text_pipeline.models import TextDraft
from lexiflow_core.text_pipeline.routing import resolve_source_route
from lexiflow_core.text_pipeline.types import TextId

LARGE_PASTE_THRESHOLD = 50_000
PROVISIONAL_TITLE = "Untitled"


class DuplicateWarning(Exception):
    """Raised when pasted content or URL matches an existing text."""

    def __init__(self, existing_id: UUID) -> None:
        self.existing_id = existing_id
        super().__init__(f"duplicate text: {existing_id}")


class LargePasteRequiresConfirmation(Exception):
    """Raised when pasted content exceeds the soft size guard without confirmation."""


class TextPipeline:
    def __init__(
        self,
        data_root: Path,
        *,
        index: LibraryIndex | None = None,
        job_service: JobService | None = None,
        text_repository: TextRepository | None = None,
        language_detector: LanguageDetector | None = None,
    ) -> None:
        self._data_root = data_root
        self._index = index if index is not None else LibraryIndex(data_root)
        self._jobs = job_service if job_service is not None else JobService(data_root)
        self._texts = (
            text_repository
            if text_repository is not None
            else TextRepository(data_root, self._index)
        )
        self._detector = language_detector
        self._duplicates = DuplicateChecker(self._index)

    def submit_new_text(self, draft: TextDraft) -> TextId:
        """Validate draft, create provisional text, and enqueue staged generation."""
        is_large = len(draft.pasted_content) > LARGE_PASTE_THRESHOLD
        if is_large and not draft.confirmed_large_paste:
            raise LargePasteRequiresConfirmation()

        if not draft.ignore_duplicate:
            existing = self._duplicates.find_duplicate(
                target_language=draft.target_language,
                pasted_content=draft.pasted_content,
                source_url=draft.source_url,
            )
            if existing is not None:
                raise DuplicateWarning(existing)

        detected = None
        if self._detector is not None:
            detected = self._detector.detect(draft.pasted_content)
        source_route = resolve_source_route(
            input_tab=draft.input_tab,
            detected_language=detected,
            native_language=draft.native_language,
            target_language=draft.target_language,
        )
        route_value = (
            SOURCE_ROUTE_NATIVE if source_route == "native" else SOURCE_ROUTE_TARGET
        )

        record = self._texts.create_text(
            CreateTextRequest(
                title=PROVISIONAL_TITLE,
                group=draft.group,
                target_language=draft.target_language,
                native_language=draft.native_language,
                body=draft.pasted_content,
                source_url=draft.source_url,
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
