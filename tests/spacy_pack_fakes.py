"""Shared fakes for spaCy pack install tests."""

from __future__ import annotations

from pathlib import Path

from lexiflow_core.languages.spacy_pack import install_spacy_pack


class FakeNlp:
    def to_disk(self, path: Path) -> None:
        path.mkdir(parents=True, exist_ok=True)
        (path / "meta.json").write_text("{}")


def fake_ensure_model(_model_name: str) -> None:
    return None


def fake_load_model(_model_name: str) -> FakeNlp:
    return FakeNlp()


def fake_install_spacy_pack(parent, *, data_root: Path, iso: str, **_kwargs) -> bool:
    install_spacy_pack(
        data_root,
        iso,
        ensure_model=fake_ensure_model,
        load_model=fake_load_model,
    )
    return True
