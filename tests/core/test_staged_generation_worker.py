"""Integration test for cleanup → translate worker chain."""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from threading import Thread

from lexiflow_core.config.paths import meta_path, variant_path
from lexiflow_core.embeddings.fake import FakeEmbedder
from lexiflow_core.jobs.models import JobStatus, JobType
from lexiflow_core.jobs.runner import run_worker_loop
from lexiflow_core.jobs.service import JobService
from lexiflow_core.library.library_coordinator import LibraryCoordinator
from lexiflow_core.library.models import CreateTextRequest
from lexiflow_core.library.text_metadata import load_text_metadata
from lexiflow_core.library.text_repository import TextRepository
from lexiflow_core.llm.fake import FakeLLM
from lexiflow_core.llm.ollama import OllamaLLM
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


def test_worker_markdownizes_messy_paste(tmp_path: Path) -> None:
    messy = "Skip ads\nHome\n\nLine one\n\nLine two"
    data_root = tmp_path / "LexiFlow"
    coordinator, index = LibraryCoordinator.open(data_root)
    del coordinator
    jobs = JobService(data_root)
    pipeline = TextPipeline(data_root, index=index, job_service=jobs)
    text_id = pipeline.submit_new_text(
        TextDraft(
            title="Article",
            group="News",
            pasted_content=messy,
            input_tab=InputTab.NATIVE,
            native_language="en",
            target_language="es",
        )
    )
    run_worker_loop(
        jobs,
        FakeLLM(
            responses=[
                "# Article\n\nLine one\n\nLine two",
                "# Titulo\n\ncuerpo",
            ]
        ),
        data_root=data_root,
    )
    repo = TextRepository(data_root, index)
    record = repo.get_text(text_id)
    native = variant_path(Path(record.folder), "native").read_text(encoding="utf-8")
    assert native.startswith("# Article")
    assert "Skip ads" not in native


def test_worker_staged_generation_with_ollama_llm(tmp_path: Path) -> None:
    responses = ["# Native Title\n\nnative body", "# Titulo\n\ncuerpo"]
    response_index = {"i": 0}

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:
            body = responses[response_index["i"]]
            response_index["i"] += 1
            payload = json.dumps({"response": body}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def log_message(self, format: str, *args: object) -> None:
            del format, args

    server = HTTPServer(("127.0.0.1", 0), Handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    base_url = f"http://{host}:{port}"

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
    try:
        llm = OllamaLLM(base_url=base_url)
        run_worker_loop(
            jobs,
            llm,
            embedder=FakeEmbedder(),
            data_root=data_root,
        )
    finally:
        server.shutdown()
        thread.join(timeout=5)

    repo = TextRepository(data_root, index)
    record = repo.get_text(text_id)
    folder = Path(record.folder)
    translated = variant_path(folder, "translated").read_text(encoding="utf-8")
    assert translated.startswith("# Titulo")
    metadata = load_text_metadata(meta_path(folder))
    assert metadata.title == "Titulo"
    listed = jobs.list_jobs()
    embed_jobs = [j for j in listed if j.job_type == JobType.EMBED]
    assert len(embed_jobs) == 1
    assert embed_jobs[0].status == JobStatus.COMPLETED


def test_worker_fails_translate_when_llm_output_has_no_title(tmp_path: Path) -> None:
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
        FakeLLM(
            responses=[
                "# Native Title\n\nnative body",
                "plain body without heading",
            ]
        ),
        data_root=data_root,
    )

    repo = TextRepository(data_root, index)
    record = repo.get_text(text_id)
    folder = Path(record.folder)
    assert variant_path(folder, "native").is_file()

    translate_jobs = [
        job for job in jobs.list_jobs() if job.job_type == JobType.TRANSLATE
    ]
    assert len(translate_jobs) == 1
    assert translate_jobs[0].status == JobStatus.FAILED
    assert translate_jobs[0].error_message is not None
    assert "document title" in translate_jobs[0].error_message.lower()
    assert not variant_path(folder, "translated").exists()


def test_worker_runs_target_route_cleanup_then_translate(tmp_path: Path) -> None:
    data_root = tmp_path / "LexiFlow"
    coordinator, index = LibraryCoordinator.open(data_root)
    del coordinator
    jobs = JobService(data_root)
    pipeline = TextPipeline(data_root, index=index, job_service=jobs)
    text_id = pipeline.submit_new_text(
        TextDraft(
            title="Spanish article",
            group="News",
            pasted_content="texto en espanol",
            input_tab=InputTab.TARGET,
            native_language="en",
            target_language="es",
        )
    )
    run_worker_loop(
        jobs,
        FakeLLM(
            responses=[
                "# Articulo\n\ntexto en espanol",
                "# Article\n\nenglish body",
                "# Articulo\n\ncuerpo en espanol",
            ]
        ),
        data_root=data_root,
    )
    repo = TextRepository(data_root, index)
    record = repo.get_text(text_id)
    folder = Path(record.folder)
    native = variant_path(folder, "native").read_text(encoding="utf-8")
    translated = variant_path(folder, "translated").read_text(encoding="utf-8")
    assert native.startswith("# Article")
    assert translated.startswith("# Articulo")
    assert native != translated


def test_worker_leaves_translated_missing_when_plain_translate_llm_fails(
    tmp_path: Path,
) -> None:
    from lexiflow_core.jobs.handlers.cleanup import TRANSLATE_PHASE_PLAIN
    from lexiflow_core.jobs.models import JobRequest
    from lexiflow_core.llm.unavailable import UnavailableLLM

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
            body="body",
        )
    )
    repo.write_native_variant(record.id, "# Native\n\ncontent")
    jobs = JobService(data_root)
    jobs.enqueue(
        JobRequest(
            job_type=JobType.TRANSLATE,
            payload={"text_id": str(record.id), "phase": TRANSLATE_PHASE_PLAIN},
        )
    )

    run_worker_loop(
        jobs,
        UnavailableLLM("LLM not configured for tests"),
        data_root=data_root,
    )

    folder = Path(record.folder)
    assert not variant_path(folder, "translated").exists()
    translate_jobs = [
        job for job in jobs.list_jobs() if job.job_type == JobType.TRANSLATE
    ]
    assert len(translate_jobs) == 1
    assert translate_jobs[0].status == JobStatus.FAILED
