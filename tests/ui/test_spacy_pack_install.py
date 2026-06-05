"""Tests for modal spaCy language-pack install."""

from __future__ import annotations

from pathlib import Path

import pytest
from lexiflow_core.languages.spacy_pack import SpacyPackError
from lexiflow_core.vocabulary.lemma_resolution import (
    spacy_pack_available,
    spacy_pack_dir,
)
from lexiflow_ui.spacy_pack_install import install_spacy_pack_with_progress
from PySide6.QtWidgets import QProgressDialog, QWidget

from tests.spacy_pack_fakes import fake_ensure_model, fake_load_model


def test_install_spacy_pack_with_progress_writes_pack(qtbot, tmp_path: Path) -> None:
    data_root = tmp_path / "library"
    parent = QWidget()
    qtbot.addWidget(parent)

    ok = install_spacy_pack_with_progress(
        parent,
        data_root=data_root,
        iso="es",
        ensure_model=fake_ensure_model,
        load_model=fake_load_model,
    )

    assert ok is True
    assert spacy_pack_available(data_root, "es")
    assert (spacy_pack_dir(data_root, "es") / "meta.json").is_file()


def test_install_spacy_pack_with_progress_failure_returns_false(
    qtbot, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    data_root = tmp_path / "library"
    parent = QWidget()
    qtbot.addWidget(parent)
    critical_messages: list[str] = []

    def capture_critical(_parent, _title: str, message: str) -> int:
        critical_messages.append(message)
        return 0

    monkeypatch.setattr(
        "lexiflow_ui.spacy_pack_install.QMessageBox.critical",
        capture_critical,
    )

    def failing_ensure(_model_name: str) -> None:
        raise SpacyPackError("download failed")

    ok = install_spacy_pack_with_progress(
        parent,
        data_root=data_root,
        iso="es",
        ensure_model=failing_ensure,
        load_model=fake_load_model,
    )

    assert ok is False
    assert not spacy_pack_available(data_root, "es")
    assert critical_messages == ["download failed"]


def test_install_spacy_pack_with_progress_shows_status_lines(
    qtbot, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    progress_labels: list[str] = []
    original_set_label_text = QProgressDialog.setLabelText

    def track_label_text(self: QProgressDialog, text: str) -> None:
        progress_labels.append(text)
        original_set_label_text(self, text)

    monkeypatch.setattr(QProgressDialog, "setLabelText", track_label_text)
    data_root = tmp_path / "library"
    parent = QWidget()
    qtbot.addWidget(parent)

    ok = install_spacy_pack_with_progress(
        parent,
        data_root=data_root,
        iso="es",
        ensure_model=fake_ensure_model,
        load_model=fake_load_model,
    )

    assert ok is True
    assert any(
        "Downloading language pack for Spanish" in label
        and "Downloading es_core_news_sm" in label
        for label in progress_labels
    )
