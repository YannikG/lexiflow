"""Tests for llama-server startup error messages."""

from __future__ import annotations

from lexiflow_ui.llama_server_errors import llama_server_startup_error


def test_llama_server_startup_error_maps_hf_auth_failure() -> None:
    stderr = (
        "get_repo_commit: error: GET failed (401): Invalid username or password.\n"
        "failed to download model from Hugging Face"
    )

    message = llama_server_startup_error(stderr)

    assert "hugging face access token" in message.lower()
    assert "language model" in message.lower()


def test_llama_server_startup_error_maps_missing_repo() -> None:
    stderr = (
        "get_repo_commit: error: GET failed (404): Repository not found.\n"
        "failed to download model from Hugging Face"
    )

    message = llama_server_startup_error(stderr)

    assert "not found" in message.lower()
    assert "language model" in message.lower()
    assert "access token" not in message.lower()


def test_llama_server_startup_error_maps_invalid_model_spec() -> None:
    stderr = (
        "get_hf_plan: no GGUF files found in repository ggml-org/gemma-4-E2B-it-GGUF\n"
        "failed to download model from Hugging Face"
    )

    message = llama_server_startup_error(stderr)

    assert "invalid" in message.lower()
    assert "language model" in message.lower()
    assert "access token" not in message.lower()


def test_llama_server_startup_error_maps_generic_hf_download_failure() -> None:
    stderr = "failed to download model from Hugging Face: connection reset"

    message = llama_server_startup_error(stderr)

    assert "failed to download" in message.lower()
    assert "language model" in message.lower()
    assert "access token required" not in message.lower()


def test_llama_server_startup_error_maps_projector_compat_failure() -> None:
    stderr = (
        "load_hparams: clip.vision.projector_type = 'gemma4uv'\n"
        "clip.cpp:4391: Unknown projector type"
    )

    message = llama_server_startup_error(stderr)

    assert "update lexiflow" in message.lower()
    assert "native llm" in message.lower() or "language model" in message.lower()
    assert "unknown projector type" not in message.lower()


def test_llama_server_startup_error_maps_unknown_model_architecture() -> None:
    stderr = (
        "llama_model_load: error loading model architecture: "
        "unknown model architecture: 'gemma4'"
    )

    message = llama_server_startup_error(stderr)

    assert "update lexiflow" in message.lower()
    assert "native llm" in message.lower() or "language model" in message.lower()
    assert "gemma4" not in message.lower()
