"""Tests for user variant edits from the reader."""

from __future__ import annotations

from pathlib import Path

import pytest
from lexiflow_core.config.paths import meta_path, variant_path
from lexiflow_core.jobs.models import JobType
from lexiflow_core.jobs.service import JobService
from lexiflow_core.library.document_title import DocumentTitleError
from lexiflow_core.library.library_coordinator import LibraryCoordinator
from lexiflow_core.library.models import CreateTextRequest, TextRecord
from lexiflow_core.library.text_metadata import load_text_metadata
from lexiflow_core.library.text_repository import TextRepository


def _create_text_with_translated(
    tmp_path: Path,
) -> tuple[Path, TextRepository, JobService, TextRecord]:
    data_root = tmp_path / "LexiFlow"
    coordinator, index = LibraryCoordinator.open(data_root)
    del coordinator
    repo = TextRepository(data_root, index)
    record = repo.create_text(
        CreateTextRequest(
            title="Untitled",
            group="News",
            target_language="es",
            native_language="en",
            body="hola",
        )
    )
    translated = "# Traducción\n\nCuerpo traducido."
    record = repo.apply_translated_variant(record.id, translated)
    jobs = JobService(data_root)
    return data_root, repo, jobs, record


def test_apply_translated_variant_does_not_update_metadata_title(
    tmp_path: Path,
) -> None:
    data_root, repo, _, record = _create_text_with_translated(tmp_path)
    assert record.title == "Untitled"

    fresh = repo.create_text(
        CreateTextRequest(
            title="Provisional",
            group="News",
            target_language="es",
            native_language="en",
            body="hola",
        )
    )
    translated = repo.apply_translated_variant(
        fresh.id,
        "# Titulo LLM\n\nCuerpo traducido.",
    )

    assert translated.title == "Provisional"


def test_save_variant_edit_writes_translated_markdown(tmp_path: Path) -> None:
    data_root, repo, _, record = _create_text_with_translated(tmp_path)
    edited = "# Nueva traducción\n\nTexto editado."

    repo.save_variant_edit(record.id, "translated", edited)

    path = variant_path(Path(record.folder), "translated")
    assert path.read_text(encoding="utf-8") == edited


def test_save_variant_edit_keeps_metadata_title_from_llm_not_user_h1(
    tmp_path: Path,
) -> None:
    data_root, repo, _, record = _create_text_with_translated(tmp_path)
    assert record.title == "Untitled"

    updated = repo.save_variant_edit(
        record.id,
        "translated",
        "# Otro título del usuario\n\nTexto editado.",
    )

    assert updated.title == "Untitled"
    reloaded = repo.get_text(record.id)
    assert reloaded.title == "Untitled"


def test_save_variant_edit_updates_library_title_when_provided(tmp_path: Path) -> None:
    data_root, repo, _, record = _create_text_with_translated(tmp_path)

    updated = repo.save_variant_edit(
        record.id,
        "translated",
        "# Traducción\n\nCuerpo traducido.",
        library_title="Nuevo título",
    )

    assert updated.title == "Nuevo título"
    reloaded = repo.get_text(record.id)
    assert reloaded.title == "Nuevo título"


def test_save_variant_edit_updates_source_url_when_requested(tmp_path: Path) -> None:
    data_root, repo, _, record = _create_text_with_translated(tmp_path)
    assert record.source_url is None

    updated = repo.save_variant_edit(
        record.id,
        "translated",
        "# Traducción\n\nCuerpo traducido.",
        source_url="https://example.com/article",
        update_source_url=True,
    )

    assert updated.source_url == "https://example.com/article"
    reloaded = repo.get_text(record.id)
    assert reloaded.source_url == "https://example.com/article"


def test_save_variant_edit_clears_source_url_when_blank(tmp_path: Path) -> None:
    data_root = tmp_path / "LexiFlow"
    coordinator, index = LibraryCoordinator.open(data_root)
    del coordinator
    repo = TextRepository(data_root, index)
    record = repo.create_text(
        CreateTextRequest(
            title="Untitled",
            group="News",
            target_language="es",
            native_language="en",
            body="hola",
            source_url="https://example.com/old",
        )
    )
    record = repo.apply_translated_variant(record.id, "# Traducción\n\nCuerpo.")

    updated = repo.save_variant_edit(
        record.id,
        "translated",
        "# Traducción\n\nCuerpo.",
        source_url=None,
        update_source_url=True,
    )

    assert updated.source_url is None
    reloaded = repo.get_text(record.id)
    assert reloaded.source_url is None


def test_save_variant_edit_keeps_source_url_without_update_flag(tmp_path: Path) -> None:
    data_root = tmp_path / "LexiFlow"
    coordinator, index = LibraryCoordinator.open(data_root)
    del coordinator
    repo = TextRepository(data_root, index)
    record = repo.create_text(
        CreateTextRequest(
            title="Untitled",
            group="News",
            target_language="es",
            native_language="en",
            body="hola",
            source_url="https://example.com/article",
        )
    )
    record = repo.apply_translated_variant(record.id, "# Traducción\n\nCuerpo.")

    updated = repo.save_variant_edit(
        record.id,
        "translated",
        "# Traducción\n\nTexto editado.",
    )

    assert updated.source_url == "https://example.com/article"


def test_save_variant_edit_rejects_invalid_library_title(tmp_path: Path) -> None:
    data_root, repo, _, record = _create_text_with_translated(tmp_path)

    with pytest.raises(DocumentTitleError):
        repo.save_variant_edit(
            record.id,
            "translated",
            "# Traducción\n\nCuerpo traducido.",
            library_title="Bad # title",
        )


def test_save_variant_edit_does_not_enqueue_translate_job(tmp_path: Path) -> None:
    data_root, repo, jobs, record = _create_text_with_translated(tmp_path)
    before = jobs.list_jobs()
    translate_before = [job for job in before if job.job_type == JobType.TRANSLATE]

    repo.save_variant_edit(
        record.id,
        "translated",
        "# Nueva traducción\n\nTexto editado.",
    )

    after = jobs.list_jobs()
    translate_after = [job for job in after if job.job_type == JobType.TRANSLATE]
    assert len(translate_after) == len(translate_before)


def test_apply_native_variant_sets_metadata_title_when_autogenerate(
    tmp_path: Path,
) -> None:
    data_root = tmp_path / "LexiFlow"
    coordinator, index = LibraryCoordinator.open(data_root)
    del coordinator
    repo = TextRepository(data_root, index)
    record = repo.create_text(
        CreateTextRequest(
            title="Untitled",
            group="News",
            target_language="es",
            native_language="en",
            body="raw",
            autogenerate_title=True,
        )
    )
    folder = Path(record.folder)

    updated = repo.apply_native_variant(record.id, "# Native H1\n\nbody")

    assert updated.title == "Native H1"
    metadata = load_text_metadata(meta_path(folder))
    assert metadata.title == "Native H1"
    assert metadata.autogenerate_title is False
    indexed = index.get_by_id(record.id)
    assert indexed is not None
    assert indexed.title == "Native H1"


def test_apply_native_variant_skips_title_when_user_provided(
    tmp_path: Path,
) -> None:
    data_root = tmp_path / "LexiFlow"
    coordinator, index = LibraryCoordinator.open(data_root)
    del coordinator
    repo = TextRepository(data_root, index)
    record = repo.create_text(
        CreateTextRequest(
            title="User title",
            group="News",
            target_language="es",
            native_language="en",
            body="raw",
            autogenerate_title=False,
        )
    )

    updated = repo.apply_native_variant(record.id, "# Cleanup H1\n\nbody")

    assert updated.title == "User title"


def test_apply_native_variant_normalizes_autogenerated_title(tmp_path: Path) -> None:
    data_root = tmp_path / "LexiFlow"
    coordinator, index = LibraryCoordinator.open(data_root)
    del coordinator
    repo = TextRepository(data_root, index)
    record = repo.create_text(
        CreateTextRequest(
            title="Untitled",
            group="News",
            target_language="es",
            native_language="en",
            body="raw",
            autogenerate_title=True,
        )
    )

    updated = repo.apply_native_variant(record.id, "#  Spaced title  \n\nbody")

    assert updated.title == "Spaced title"


def test_apply_native_variant_clears_autogenerate_after_first_title_sync(
    tmp_path: Path,
) -> None:
    data_root = tmp_path / "LexiFlow"
    coordinator, index = LibraryCoordinator.open(data_root)
    del coordinator
    repo = TextRepository(data_root, index)
    record = repo.create_text(
        CreateTextRequest(
            title="Untitled",
            group="News",
            target_language="es",
            native_language="en",
            body="raw",
            autogenerate_title=True,
        )
    )

    repo.apply_native_variant(record.id, "# First H1\n\nbody")
    repo.apply_native_variant(record.id, "# Second H1\n\nbody")

    reloaded = repo.get_text(record.id)
    assert reloaded.title == "First H1"


def test_save_variant_edit_clears_autogenerate_when_library_title_set(
    tmp_path: Path,
) -> None:
    data_root = tmp_path / "LexiFlow"
    coordinator, index = LibraryCoordinator.open(data_root)
    del coordinator
    repo = TextRepository(data_root, index)
    record = repo.create_text(
        CreateTextRequest(
            title="Untitled",
            group="News",
            target_language="es",
            native_language="en",
            body="raw",
            autogenerate_title=True,
        )
    )

    updated = repo.save_variant_edit(
        record.id,
        "native",
        "# Native\n\nbody",
        library_title="User chosen title",
    )

    assert updated.title == "User chosen title"
    metadata = load_text_metadata(meta_path(Path(record.folder)))
    assert metadata.autogenerate_title is False
