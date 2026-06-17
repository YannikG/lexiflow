"""Download and install spaCy language packs under the data root."""

from __future__ import annotations

import shutil
import sys
import tempfile
import urllib.request
import zipfile
from collections.abc import Callable
from pathlib import Path
from typing import Protocol, cast
from urllib.parse import urljoin

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


def spacy_model_wheel_url(model_name: str) -> str:
    """Return the official spaCy model wheel URL for the installed spaCy version."""
    from spacy import about
    from spacy.cli.download import get_compatibility, get_model_filename, get_version

    compatibility = get_compatibility()
    version = get_version(model_name, compatibility)
    filename = get_model_filename(model_name, version)
    base_url = about.__download_url__
    if not base_url.endswith("/"):
        base_url = f"{base_url}/"
    return urljoin(base_url, filename)


def load_spacy_model_from_wheel_url(
    model_name: str,
    download_url: str,
    *,
    urlretrieve: Callable[[str, str], object] | None = None,
) -> SpacyPackModel:
    """Download a spaCy model wheel and load it without invoking pip."""
    import spacy

    fetch = urlretrieve or urllib.request.urlretrieve
    with tempfile.TemporaryDirectory() as tmp:
        wheel_path = Path(tmp) / download_url.rsplit("/", 1)[-1]
        fetch(download_url, str(wheel_path))
        extract_dir = Path(tmp) / "wheel"
        extract_dir.mkdir()
        with zipfile.ZipFile(wheel_path) as archive:
            archive.extractall(extract_dir)
        model_dir = extract_dir / model_name
        if not model_dir.is_dir():
            raise SpacyPackError(f"model {model_name!r} missing from downloaded wheel")
        return cast(SpacyPackModel, spacy.load(str(model_dir)))


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
    import spacy

    def report(message: str, *, fraction: float) -> None:
        if on_status is not None:
            on_status(message)
        if on_progress is not None:
            on_progress(fraction)

    if spacy.util.is_package(model_name):
        report(f"Loading {model_name}…", fraction=0.6)
        return cast(SpacyPackModel, spacy.load(model_name))

    if getattr(sys, "frozen", False):
        report(f"Downloading {model_name}…", fraction=0.1)
        download_url = spacy_model_wheel_url(model_name)
        nlp = load_spacy_model_from_wheel_url(model_name, download_url)
        report(f"Loading {model_name}…", fraction=0.6)
        return nlp

    from spacy.cli import download as spacy_download  # type: ignore[attr-defined]

    report(f"Downloading {model_name} from spaCy…", fraction=0.1)
    spacy_download(model_name)
    report(f"Loading {model_name}…", fraction=0.6)
    return cast(SpacyPackModel, spacy.load(model_name))
