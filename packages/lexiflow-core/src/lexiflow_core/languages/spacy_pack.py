"""Download and install spaCy language packs under the data root."""

from __future__ import annotations

import shutil
from collections.abc import Callable
from pathlib import Path
from typing import Protocol, cast

from lexiflow_core.vocabulary.lemma_resolution import (
    spacy_pack_available,
    spacy_pack_dir,
)

_SPECIAL_SPACY_MODELS: dict[str, str] = {
    "zh": "zh_core_web_sm",
}


class SpacyPackError(Exception):
    """Raised when a spaCy pack cannot be installed."""


class SpacyPackModel(Protocol):
    """spaCy pipeline object that can be exported to a pack directory."""

    def to_disk(self, path: Path) -> None: ...


def spacy_model_name(iso: str) -> str:
    """Return the spaCy pipeline name used for a target ISO 639-1 code."""
    return _SPECIAL_SPACY_MODELS.get(iso, f"{iso}_core_news_sm")


def install_spacy_pack(
    data_root: Path,
    iso: str,
    *,
    ensure_model: Callable[[str], None] | None = None,
    load_model: Callable[[str], SpacyPackModel] | None = None,
    on_status: Callable[[str], None] | None = None,
    on_progress: Callable[[float], None] | None = None,
) -> Path:
    """Download a spaCy model when needed and export it to the pack directory."""
    language_code = iso.strip()
    if not language_code:
        raise SpacyPackError("language code is required")

    dest = spacy_pack_dir(data_root, language_code)
    if spacy_pack_available(data_root, language_code):
        return dest

    model_name = spacy_model_name(language_code)

    def report_status(message: str, *, fraction: float | None = None) -> None:
        if on_status is not None:
            on_status(message)
        if on_progress is not None and fraction is not None:
            on_progress(fraction)

    try:
        if ensure_model is not None and load_model is not None:
            report_status(f"Downloading {model_name}…", fraction=0.1)
            ensure_model(model_name)
            report_status(f"Loading {model_name}…", fraction=0.6)
            nlp = load_model(model_name)
        else:
            nlp = _default_load_after_download(
                model_name,
                on_status=on_status,
                on_progress=on_progress,
            )
    except ImportError as exc:
        raise SpacyPackError(
            "spaCy is not installed. Install spaCy to download language packs."
        ) from exc
    except OSError as exc:
        raise SpacyPackError(
            f"spaCy model {model_name!r} is not available for {language_code}"
        ) from exc
    except SpacyPackError:
        raise
    except Exception as exc:
        message = f"failed to install spaCy pack for {language_code}"
        raise SpacyPackError(message) from exc

    if dest.exists():
        if dest.is_dir():
            shutil.rmtree(dest)
        else:
            dest.unlink()
    dest.parent.mkdir(parents=True, exist_ok=True)
    report_status("Exporting language pack…", fraction=0.9)
    nlp.to_disk(dest)
    report_status("Language pack ready.", fraction=1.0)
    return dest


def _default_load_after_download(
    model_name: str,
    *,
    on_status: Callable[[str], None] | None = None,
    on_progress: Callable[[float], None] | None = None,
) -> SpacyPackModel:
    import spacy  # type: ignore[import-not-found]
    from spacy.cli import download as spacy_download  # type: ignore[import-not-found]

    def report(message: str, *, fraction: float) -> None:
        if on_status is not None:
            on_status(message)
        if on_progress is not None:
            on_progress(fraction)

    if not spacy.util.is_package(model_name):
        report(f"Downloading {model_name} from spaCy…", fraction=0.1)
        spacy_download(model_name)
    report(f"Loading {model_name}…", fraction=0.6)
    return cast(SpacyPackModel, spacy.load(model_name))
