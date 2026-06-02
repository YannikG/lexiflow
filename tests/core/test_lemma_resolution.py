"""Tests for spaCy-based lemma resolution."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from lexiflow_core.vocabulary.lemma_resolution import (
    resolve_lemma_with_spacy,
    spacy_pack_dir,
)


def test_resolve_lemma_with_spacy_returns_none_without_pack(tmp_path: Path) -> None:
    data_root = tmp_path / "LexiFlow"
    assert resolve_lemma_with_spacy(data_root, "es", "corriendo") is None


def test_resolve_lemma_with_spacy_uses_installed_pack(tmp_path: Path) -> None:
    data_root = tmp_path / "LexiFlow"
    pack_dir = spacy_pack_dir(data_root, "es")
    pack_dir.mkdir(parents=True)
    (pack_dir / "meta.json").write_text("{}", encoding="utf-8")

    mock_token = MagicMock()
    mock_token.lemma_ = "Correr"
    mock_doc = MagicMock()
    mock_doc.__getitem__.return_value = mock_token
    mock_doc.__bool__.return_value = True

    mock_nlp = MagicMock(return_value=mock_doc)
    mock_spacy = MagicMock()
    mock_spacy.load.return_value = mock_nlp

    with patch.dict("sys.modules", {"spacy": mock_spacy}):
        result = resolve_lemma_with_spacy(data_root, "es", "corriendo")

    assert result is not None
    assert result.lemma == "correr"
    mock_spacy.load.assert_called_once_with(str(pack_dir))
