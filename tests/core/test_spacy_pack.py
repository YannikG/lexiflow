"""Tests for spaCy pack install helpers."""

from __future__ import annotations

import zipfile
from pathlib import Path

import pytest
from lexiflow_core.languages.spacy_pack import (
    install_spacy_pack,
    load_spacy_model_from_wheel_url,
    spacy_model_name,
    spacy_model_wheel_url,
)
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


def test_spacy_model_wheel_url_points_at_official_release() -> None:
    url = spacy_model_wheel_url("de_core_news_sm")
    assert url.startswith(
        "https://github.com/explosion/spacy-models/releases/download/"
    )
    assert "de_core_news_sm" in url
    assert url.endswith(".whl")


def test_load_spacy_model_from_wheel_url(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    sentinel = object()
    model_name = "de_core_news_sm"
    wheel_path = tmp_path / "model.whl"
    with zipfile.ZipFile(wheel_path, "w") as archive:
        archive.writestr(f"{model_name}/meta.json", '{"lang":"de"}')

    import spacy

    def fake_urlretrieve(_url: str, destination: str) -> tuple[None, None]:
        Path(destination).write_bytes(wheel_path.read_bytes())
        return None, None

    monkeypatch.setattr(spacy, "load", lambda _path: sentinel)

    loaded = load_spacy_model_from_wheel_url(
        model_name,
        "https://example.test/model.whl",
        urlretrieve=fake_urlretrieve,
    )
    assert loaded is sentinel


def test_default_load_after_download_uses_wheel_path_when_frozen(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import lexiflow_core.languages.spacy_pack as spacy_pack_module

    sentinel = object()
    monkeypatch.setattr(spacy_pack_module.sys, "frozen", True, raising=False)
    monkeypatch.setattr("spacy.util.is_package", lambda _name: False)
    monkeypatch.setattr(
        spacy_pack_module,
        "spacy_model_wheel_url",
        lambda _name: "https://example.test/model.whl",
    )
    monkeypatch.setattr(
        spacy_pack_module,
        "load_spacy_model_from_wheel_url",
        lambda _name, _url: sentinel,
    )

    loaded = spacy_pack_module._default_load_after_download("de_core_news_sm")
    assert loaded is sentinel
