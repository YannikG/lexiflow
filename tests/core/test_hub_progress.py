"""Tests for Hugging Face Hub tqdm bridging."""

from __future__ import annotations

from lexiflow_core.models.hub_progress import reporting_tqdm_factory


def test_reporting_tqdm_emits_fraction_and_log_line() -> None:
    fractions: list[float] = []
    lines: list[str] = []
    tqdm_class = reporting_tqdm_factory(
        on_fraction=fractions.append,
        on_log_line=lines.append,
    )
    with tqdm_class(total=4, desc="Downloading") as bar:
        for _ in range(4):
            bar.update(1)
    assert fractions
    assert max(fractions) == 1.0
    assert lines
    assert any("Downloading" in line for line in lines)
