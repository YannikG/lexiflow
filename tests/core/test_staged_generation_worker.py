"""Integration test for cleanup → translate worker chain."""

from __future__ import annotations

from pathlib import Path

from lexiflow_core.config.paths import meta_path, variant_path
from lexiflow_core.jobs.runner import run_worker_loop
from lexiflow_core.jobs.service import JobService
from lexiflow_core.library.library_coordinator import LibraryCoordinator
from lexiflow_core.library.text_metadata import load_text_metadata
from lexiflow_core.library.text_repository import TextRepository
from lexiflow_core.llm.fake import FakeLLM
from lexiflow_core.text_pipeline import InputTab, TextDraft, TextPipeline


def test_worker_runs_cleanup_then_translate(tmp_path: Path) -> None:
    data_root = tmp_path / "LexiFlow"
    coordinator, index = LibraryCoordinator.open(data_root)
    del coordinator
    jobs = JobService(data_root)
    pipeline = TextPipeline(data_root, index=index, job_service=jobs)
    text_id = pipeline.submit_new_text(
        TextDraft(
            title="Raw article",
            group="News",
            pasted_content="raw article",
            input_tab=InputTab.NATIVE,
            native_language="en",
            target_language="es",
        )
    )
    run_worker_loop(
        jobs,
        FakeLLM(responses=["# Native Title\n\nnative body", "# Titulo\n\ncuerpo"]),
        data_root=data_root,
    )
    repo = TextRepository(data_root, index)
    record = repo.get_text(text_id)
    folder = Path(record.folder)
    native = variant_path(folder, "native").read_text(encoding="utf-8")
    translated = variant_path(folder, "translated").read_text(encoding="utf-8")
    assert native.startswith("# Native Title")
    assert translated.startswith("# Titulo")
    metadata = load_text_metadata(meta_path(folder))
    assert metadata.title == "Titulo"
