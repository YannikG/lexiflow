"""Tests for lexiflow_worker.main."""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from threading import Thread
from unittest.mock import patch

import tomli_w
from lexiflow_core.config.settings_store import SettingsStore
from lexiflow_core.jobs.models import JobRequest, JobStatus, JobType
from lexiflow_core.jobs.service import JobService
from lexiflow_core.llm.fake import FakeLLM
from lexiflow_worker.main import main


def test_main_exits_zero_with_empty_queue(tmp_path: Path) -> None:
    with patch("lexiflow_worker.main.resolve_llm", return_value=FakeLLM()):
        assert main(["--data-root", str(tmp_path)]) == 0


def test_main_completes_legacy_prompt_job(tmp_path: Path) -> None:
    job_service = JobService(tmp_path)
    job_service.enqueue(
        JobRequest(job_type=JobType.TRANSLATE, payload={"prompt": "hello"})
    )

    with patch("lexiflow_worker.main.resolve_llm", return_value=FakeLLM()):
        assert main(["--data-root", str(tmp_path)]) == 0

    jobs = JobService(tmp_path).list_jobs()
    assert len(jobs) == 1
    assert jobs[0].status == JobStatus.COMPLETED
    assert jobs[0].result == {"text": "fake completion"}


def test_main_completes_embed_job_with_fake_embedder(tmp_path: Path) -> None:
    from lexiflow_core.library.library_coordinator import LibraryCoordinator
    from lexiflow_core.library.models import CreateTextRequest
    from lexiflow_core.library.text_repository import TextRepository
    from lexiflow_core.vectors.store import VectorStore

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
    repo.apply_translated_variant(record.id, "# Traducción\n\nCuerpo.")
    job_service = JobService(data_root)
    job_service.enqueue(
        JobRequest(job_type=JobType.EMBED, payload={"text_id": str(record.id)})
    )

    with patch("lexiflow_worker.main.resolve_llm", return_value=FakeLLM()):
        assert main(["--data-root", str(data_root)]) == 0

    jobs = job_service.list_jobs()
    assert jobs[0].status == JobStatus.COMPLETED
    assert VectorStore(data_root, "es").get_text_vector(record.id) is not None


def test_main_completes_legacy_job_via_ollama_settings(tmp_path: Path) -> None:
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:
            length = int(self.headers.get("Content-Length", "0"))
            json.loads(self.rfile.read(length))
            payload = json.dumps({"response": "from ollama"}).encode()
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

    config_dir = tmp_path / "config"
    config_dir.mkdir()
    with (config_dir / "settings.toml").open("wb") as handle:
        tomli_w.dump(
            {"ollama_url": base_url},
            handle,
        )

    data_root = tmp_path / "library"
    job_service = JobService(data_root)
    job_service.enqueue(
        JobRequest(job_type=JobType.TRANSLATE, payload={"prompt": "hello"})
    )

    try:
        with patch(
            "lexiflow_worker.main.SettingsStore",
            return_value=SettingsStore(config_dir),
        ):
            assert main(["--data-root", str(data_root)]) == 0
    finally:
        server.shutdown()
        thread.join(timeout=5)

    jobs = job_service.list_jobs()
    assert jobs[0].status == JobStatus.COMPLETED
    assert jobs[0].result == {"text": "from ollama"}


def test_main_completes_simplify_job_with_fake_llm(tmp_path: Path) -> None:
    import json

    from lexiflow_core.config.paths import variant_path
    from lexiflow_core.jobs.simplify_queue import enqueue_simplify
    from lexiflow_core.library.library_coordinator import LibraryCoordinator
    from lexiflow_core.library.models import CreateTextRequest
    from lexiflow_core.library.text_repository import TextRepository

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
    repo.apply_translated_variant(record.id, "# Traducción\n\nCuerpo.")
    job_service = JobService(data_root)
    simplify_json = json.dumps(
        {
            "title": "Simple",
            "body": "Texto corto.",
            "new_words": [],
        }
    )
    enqueue_simplify(job_service, record.id, "A2")

    with patch("lexiflow_worker.main.resolve_llm", return_value=FakeLLM(simplify_json)):
        assert main(["--data-root", str(data_root)]) == 0

    folder = variant_path(Path(record.folder), "simplified-a2").parent
    simplified = variant_path(folder, "simplified-a2").read_text(encoding="utf-8")
    assert simplified.startswith("# Simple")
    jobs = job_service.list_jobs()
    assert jobs[0].status == JobStatus.COMPLETED
    assert jobs[0].job_type == JobType.SIMPLIFY


def test_main_fails_simplify_job_when_llm_disabled(tmp_path: Path) -> None:
    from lexiflow_core.config.paths import variant_path
    from lexiflow_core.jobs.simplify_queue import enqueue_simplify
    from lexiflow_core.library.library_coordinator import LibraryCoordinator
    from lexiflow_core.library.models import CreateTextRequest
    from lexiflow_core.library.text_repository import TextRepository
    from lexiflow_core.llm.disabled import DisabledLLM

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
    repo.apply_translated_variant(record.id, "# Traducción\n\nCuerpo.")
    job_service = JobService(data_root)
    enqueue_simplify(job_service, record.id, "A2")

    with patch("lexiflow_worker.main.resolve_llm", return_value=DisabledLLM()):
        assert main(["--data-root", str(data_root)]) == 0

    assert not variant_path(Path(record.folder), "simplified-a2").exists()
    jobs = job_service.list_jobs()
    assert jobs[0].status == JobStatus.FAILED
    assert jobs[0].error_message is not None


def test_main_fails_job_when_no_llm_configured(tmp_path: Path) -> None:
    data_root = tmp_path / "library"
    job_service = JobService(data_root)
    job_service.enqueue(
        JobRequest(job_type=JobType.TRANSLATE, payload={"prompt": "hello"})
    )

    assert main(["--data-root", str(data_root)]) == 0

    jobs = job_service.list_jobs()
    assert jobs[0].status == JobStatus.FAILED
    assert jobs[0].error_message is not None
    assert "not installed" in jobs[0].error_message.lower()
