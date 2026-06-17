"""Tests for user-facing job error messages."""

from __future__ import annotations

from lexiflow_core.jobs.job_errors import (
    inference_subprocess_error,
    user_facing_job_error,
)


def test_user_facing_job_error_maps_llama_server_connection_failure() -> None:
    message = user_facing_job_error("llama-server request failed: Connection refused")
    assert "not running yet" in message.lower()


def test_user_facing_job_error_maps_llama_server_install_hint() -> None:
    message = user_facing_job_error(
        "Install llama.cpp llama-server and ensure it is on PATH, or set "
        "LEXIFLOW_LLAMA_SERVER_BIN."
    )
    assert "lexiflow_llama_server_bin" in message.lower()


def test_user_facing_job_error_strips_multiline_traceback() -> None:
    raw = "Generation failed\nTraceback (most recent call last):"
    message = user_facing_job_error(raw)
    assert message == "Generation failed"


def test_inference_subprocess_error_prefers_actionable_line() -> None:
    stderr = (
        "Traceback (most recent call last):\n"
        '  File "x.py", line 1, in <module>\n'
        "Connection refused"
    )
    message = inference_subprocess_error(stderr, exit_code=1)
    assert "not running yet" in message.lower()


def test_user_facing_job_error_maps_sqlite_vec_dlopen_failure() -> None:
    message = user_facing_job_error(
        "dlopen(/Applications/LexiFlow.app/.../sqlite_vec/vec0.dylib, 0x000A): "
        "no such file"
    )
    assert "sqlite-vec extension is missing" in message.lower()


def test_user_facing_job_error_does_not_map_python_sqlite_build_error() -> None:
    message = user_facing_job_error(
        "'sqlite3.Connection' object has no attribute 'enable_load_extension'"
    )
    assert "sqlite-vec extension is missing" not in message.lower()


def test_user_facing_job_error_does_not_map_vec0_sql_error() -> None:
    message = user_facing_job_error("no such table: vec0_embeddings")
    assert "sqlite-vec extension is missing" not in message.lower()


def test_inference_subprocess_error_maps_sqlite_vec_load_failure() -> None:
    stderr = "sqlite-vec loadable vec0 not found; searched: /tmp/sqlite_vec"
    message = inference_subprocess_error(stderr, exit_code=1)
    assert "sqlite-vec extension is missing" in message.lower()


def test_user_facing_job_error_empty_message() -> None:
    message = user_facing_job_error("   ")
    assert "generation failed" in message.lower()
