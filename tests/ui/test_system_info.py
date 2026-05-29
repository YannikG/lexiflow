"""Tests for onboarding system information helpers."""

from __future__ import annotations

import platform

import pytest
from lexiflow_ui.onboarding import system_info
from lexiflow_ui.onboarding.system_info import (
    RECOMMENDED_RAM_BYTES,
    PlatformSystemInfo,
    ram_warning_message,
)


def test_ram_warning_message_returns_none_when_enough_ram() -> None:
    assert ram_warning_message(RECOMMENDED_RAM_BYTES) is None
    assert ram_warning_message(RECOMMENDED_RAM_BYTES + 1) is None


def test_ram_warning_message_reports_detected_low_ram() -> None:
    message = ram_warning_message(4 * 1024**3)

    assert message is not None
    assert "4.0 GiB" in message
    assert "continue anyway" in message.lower()


def test_ram_warning_message_reports_unknown_ram() -> None:
    message = ram_warning_message(0)

    assert message is not None
    assert "could not detect" in message.lower()
    assert "0.0 GiB" not in message


def test_platform_system_info_uses_windows_probe(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(platform, "system", lambda: "Windows")
    monkeypatch.setattr(system_info, "_windows_total_ram_bytes", lambda: 16 * 1024**3)

    assert PlatformSystemInfo().total_ram_bytes() == 16 * 1024**3
