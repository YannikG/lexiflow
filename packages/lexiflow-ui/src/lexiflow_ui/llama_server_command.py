"""Build argv for spawning llama-server."""

from __future__ import annotations


def build_llama_server_command(
    executable: str,
    *,
    hf_model: str,
    host: str,
    port: int,
    hf_token: str | None = None,
    embeddings: bool = False,
) -> list[str]:
    """Return argv to start llama-server with a pinned Hugging Face model."""
    command = [
        executable,
        "-hf",
        hf_model,
        "--host",
        host,
        "--port",
        str(port),
    ]
    if embeddings:
        command.append("--embedding")
    if hf_token:
        command.extend(["--hf-token", hf_token])
    return command
