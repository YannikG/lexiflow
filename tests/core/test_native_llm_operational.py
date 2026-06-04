"""Tests for native llama-server operational checks."""

from __future__ import annotations

from pathlib import Path

from lexiflow_core.config.settings import Settings
from lexiflow_core.llm.llama_server import (
    llama_server_binary,
    native_llm_operational,
    pinned_llama_hf_model,
)


def test_native_llm_operational_skips_check_for_ollama() -> None:
    settings = Settings(ollama_url="http://127.0.0.1:11434")

    ready, message = native_llm_operational(settings)

    assert ready is True
    assert message is None


def test_native_llm_operational_false_when_binary_missing(monkeypatch) -> None:
    monkeypatch.setattr(
        "lexiflow_core.llm.llama_server.llama_server_binary",
        lambda: None,
    )

    ready, message = native_llm_operational(Settings())

    assert ready is False
    assert message is not None
    assert "llama-server" in message.lower()


def test_native_llm_operational_true_when_binary_and_pin_present(monkeypatch) -> None:
    monkeypatch.setattr(
        "lexiflow_core.llm.llama_server.llama_server_binary",
        lambda: "/usr/bin/llama-server",
    )

    ready, message = native_llm_operational(Settings())

    assert ready is True
    assert message is None


def test_pinned_llama_hf_model_reads_bundled_lock() -> None:
    spec = pinned_llama_hf_model()

    assert spec
    assert ":" in spec


def test_path_directories_appends_homebrew_when_missing_from_path(monkeypatch) -> None:
    from lexiflow_core.llm.llama_server import _path_directories

    monkeypatch.setenv("PATH", "/usr/bin:/bin")

    directories = _path_directories()

    assert directories[:2] == ("/usr/bin", "/bin")
    assert "/opt/homebrew/bin" in directories
    assert "/usr/local/bin" in directories


def test_path_directories_does_not_duplicate_path_entries(monkeypatch) -> None:
    from lexiflow_core.llm.llama_server import _path_directories

    monkeypatch.setenv("PATH", "/opt/homebrew/bin:/usr/bin")

    directories = _path_directories()

    assert directories.count("/opt/homebrew/bin") == 1


def test_llama_server_binary_returns_path_or_none() -> None:
    result = llama_server_binary()

    assert result is None or isinstance(result, str)


def test_llama_server_runtime_env_includes_binary_and_path(monkeypatch) -> None:
    from lexiflow_core.llm.llama_server import llama_server_runtime_env

    monkeypatch.setenv("PATH", "/usr/bin")
    monkeypatch.setattr(
        "lexiflow_core.llm.llama_server.llama_server_binary",
        lambda: "/opt/homebrew/bin/llama-server",
    )
    monkeypatch.setattr(
        "lexiflow_core.llm.llama_server._path_directories",
        lambda: ("/opt/homebrew/bin", "/usr/bin"),
    )

    env = llama_server_runtime_env()

    assert env["LEXIFLOW_LLAMA_SERVER_BIN"] == "/opt/homebrew/bin/llama-server"
    assert env["PATH"] == "/opt/homebrew/bin:/usr/bin"


def test_llama_server_binary_searches_path_directories(
    monkeypatch, tmp_path: Path
) -> None:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    fake_binary = bin_dir / "llama-server"
    fake_binary.write_text("")
    fake_binary.chmod(0o755)
    monkeypatch.delenv("LEXIFLOW_LLAMA_SERVER_BIN", raising=False)
    monkeypatch.setenv("PATH", str(tmp_path / "empty"))
    monkeypatch.setattr(
        "lexiflow_core.llm.llama_server._path_directories",
        lambda: (str(bin_dir),),
    )

    assert llama_server_binary() == str(fake_binary)


def test_llama_server_binary_prefers_earlier_path_entry(
    monkeypatch, tmp_path: Path
) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"
    first.mkdir()
    second.mkdir()
    first_binary = first / "llama-server"
    first_binary.write_text("")
    first_binary.chmod(0o755)
    second_binary = second / "llama-server"
    second_binary.write_text("")
    second_binary.chmod(0o755)
    monkeypatch.delenv("LEXIFLOW_LLAMA_SERVER_BIN", raising=False)
    monkeypatch.setattr(
        "lexiflow_core.llm.llama_server._path_directories",
        lambda: (str(first), str(second)),
    )

    assert llama_server_binary() == str(first_binary)


def test_llama_server_binary_prefers_lexiflow_env_override(
    monkeypatch, tmp_path: Path
) -> None:
    override = tmp_path / "custom-llama-server"
    override.write_text("")
    override.chmod(0o755)
    other = tmp_path / "other-llama-server"
    other.write_text("")
    other.chmod(0o755)
    monkeypatch.setenv("LEXIFLOW_LLAMA_SERVER_BIN", str(override))
    monkeypatch.setattr(
        "lexiflow_core.llm.llama_server._path_directories",
        lambda: (str(other.parent),),
    )

    assert llama_server_binary() == str(override)


def test_llama_server_binary_resolves_windows_exe(monkeypatch, tmp_path: Path) -> None:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    fake_binary = bin_dir / "llama-server.exe"
    fake_binary.write_text("")
    fake_binary.chmod(0o755)
    monkeypatch.setattr(
        "lexiflow_core.llm.llama_server._llama_server_executable_name",
        lambda: "llama-server.exe",
    )
    monkeypatch.delenv("LEXIFLOW_LLAMA_SERVER_BIN", raising=False)
    monkeypatch.setattr(
        "lexiflow_core.llm.llama_server._path_directories",
        lambda: (str(bin_dir),),
    )

    assert llama_server_binary() == str(fake_binary)


def test_llama_server_binary_uses_bundled_path_when_frozen(
    monkeypatch, tmp_path: Path
) -> None:
    import sys

    bundled = tmp_path / "bin" / "llama-server"
    bundled.parent.mkdir()
    bundled.write_text("")
    bundled.chmod(0o755)
    monkeypatch.delenv("LEXIFLOW_LLAMA_SERVER_BIN", raising=False)
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path), raising=False)
    monkeypatch.setattr(
        "lexiflow_core.llm.llama_server._path_directories",
        lambda: (str(tmp_path / "empty"),),
    )

    assert llama_server_binary() == str(bundled)
