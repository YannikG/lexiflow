"""Tests for spaCy pack install helpers."""

from __future__ import annotations

from pathlib import Path

from lexiflow_core.languages.spacy_pack import install_spacy_pack, spacy_model_name
from lexiflow_core.vocabulary.lemma_resolution import spacy_pack_available
from tests.spacy_pack_fakes import fake_ensure_model, fake_load_model


def test_spacy_model_name_uses_special_case_for_chinese() -> None:
    assert spacy_model_name("zh") == "zh_core_web_sm"
    assert spacy_model_name("es") == "es_core_news_sm"


def test_install_spacy_pack_with_injected_loaders(tmp_path: Path) -> None:
    data_root = tmp_path / "library"

    install_spacy_pack(
        data_root,
        "es",
        ensure_model=fake_ensure_model,
        load_model=fake_load_model,
    )

    assert spacy_pack_available(data_root, "es")
