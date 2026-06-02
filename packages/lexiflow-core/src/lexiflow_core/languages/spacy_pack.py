"""Download and install spaCy language packs under the data root."""

from __future__ import annotations

import shutil
from collections.abc import Callable
from pathlib import Path
from typing import Protocol

from lexiflow_core.vocabulary.lemma_resolution import (
    spacy_pack_available,
    spacy_pack_dir,
)

_SPECIAL_SPACY_MODELS: dict[str, str] = {
    "zh": "zh_core_web_sm",
}


class SpacyPackError(Exception):
    """Raised when a spaCy pack cannot be installed."""


class _SupportsToDisk(Protocol):
    def to_disk(self, path: Path) -> None: ...


def spacy_model_name(iso: str) -> str:
    """Return the spaCy pipeline name used for a target ISO 639-1 code."""
    return _SPECIAL_SPACY_MODELS.get(iso, f"{iso}_core_news_sm")


def install_spacy_pack(
    data_root: Path,
    iso: str,
    *,
    ensure_model: Callable[[str], None] | None = None,
    load_model: Callable[[str], _SupportsToDisk] | None = None,
) -> Path:
    """Download a spaCy model when needed and export it to the pack directory."""
    language_code = iso.strip()
    if not language_code:
        raise SpacyPackError("language code is required")

    dest = spacy_pack_dir(data_root, language_code)
    if spacy_pack_available(data_root, language_code):
        return dest

    model_name = spacy_model_name(language_code)
    try:
        if ensure_model is not None and load_model is not None:
            ensure_model(model_name)
            nlp = load_model(model_name)
        else:
            nlp = _default_load_after_download(model_name)
    except ImportError as exc:
        raise SpacyPackError(
            "spaCy is not installed. Install spaCy to download language packs."
        ) from exc
    except OSError as exc:
        raise SpacyPackError(
            f"spaCy model {model_name!r} is not available for {language_code}"
        ) from exc
    except Exception as exc:
        message = f"failed to install spaCy pack for {language_code}"
        raise SpacyPackError(message) from exc

    if dest.exists():
        shutil.rmtree(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    nlp.to_disk(dest)
    return dest


def _default_load_after_download(model_name: str) -> _SupportsToDisk:
    import spacy  # type: ignore[import-not-found]
    from spacy.cli import download as spacy_download

    if not spacy.util.is_package(model_name):
        spacy_download(model_name)
    return spacy.load(model_name)
