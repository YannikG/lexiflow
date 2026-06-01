"""Tests for llama-server spawn command builder."""

from __future__ import annotations

from lexiflow_ui.llama_server_command import build_llama_server_command


def test_build_llama_server_command_uses_hf_flag() -> None:
    command = build_llama_server_command(
        "/usr/bin/llama-server",
        hf_model="ggml-org/gemma-4-E2B-it-GGUF:Q8_0",
        host="127.0.0.1",
        port=8080,
    )

    assert command == [
        "/usr/bin/llama-server",
        "-hf",
        "ggml-org/gemma-4-E2B-it-GGUF:Q8_0",
        "--host",
        "127.0.0.1",
        "--port",
        "8080",
    ]


def test_build_llama_server_command_passes_hf_token() -> None:
    command = build_llama_server_command(
        "/usr/bin/llama-server",
        hf_model="org/model:quant",
        host="127.0.0.1",
        port=8080,
        hf_token="hf_secret",
    )

    assert command[-2:] == ["--hf-token", "hf_secret"]
