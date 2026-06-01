"""Hugging Face Hub model downloads."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from huggingface_hub import snapshot_download
from huggingface_hub.errors import (
    GatedRepoError,
    HfHubHTTPError,
    LocalEntryNotFoundError,
    RepositoryNotFoundError,
    RevisionNotFoundError,
)

from lexiflow_core.models.download import (
    ModelAccessError,
    ModelPinError,
    NetworkError,
)
from lexiflow_core.models.hub_progress import reporting_tqdm_factory
from lexiflow_core.models.lockfile import ModelArtifact


class HuggingFaceModelDownloader:
    """Download pinned model revisions from the Hugging Face Hub."""

    def download(
        self,
        artifact: ModelArtifact,
        dest: Path,
        *,
        token: str | None,
        on_progress: Callable[[float], None] | None = None,
        on_log_line: Callable[[str], None] | None = None,
    ) -> None:
        dest.mkdir(parents=True, exist_ok=True)
        tqdm_class: type[Any] | None = None
        if on_progress is not None or on_log_line is not None:
            tqdm_class = reporting_tqdm_factory(
                on_fraction=on_progress,
                on_log_line=on_log_line,
            )
            if on_progress is not None:
                on_progress(0.0)
        try:
            if artifact.allow_patterns:
                snapshot_download(
                    repo_id=artifact.repo,
                    revision=artifact.revision,
                    local_dir=dest,
                    token=token,
                    allow_patterns=list(artifact.allow_patterns),
                    tqdm_class=tqdm_class,
                )
            else:
                snapshot_download(
                    repo_id=artifact.repo,
                    revision=artifact.revision,
                    local_dir=dest,
                    token=token,
                    tqdm_class=tqdm_class,
                )
        except GatedRepoError as exc:
            raise ModelAccessError(str(exc)) from exc
        except (RevisionNotFoundError, RepositoryNotFoundError) as exc:
            raise ModelPinError(
                f"invalid pin for {artifact.id} ({artifact.repo}@{artifact.revision})"
            ) from exc
        except HfHubHTTPError as exc:
            if _http_status(exc) in {401, 403}:
                raise ModelAccessError(str(exc)) from exc
            raise NetworkError(str(exc)) from exc
        except LocalEntryNotFoundError as exc:
            raise NetworkError(str(exc)) from exc
        except Exception as exc:
            message = str(exc).lower()
            if "connection" in message or "network" in message or "timeout" in message:
                raise NetworkError(str(exc)) from exc
            raise

        (dest / "revision.txt").write_text(artifact.revision, encoding="utf-8")
        if on_progress is not None:
            on_progress(1.0)


def _http_status(exc: HfHubHTTPError) -> int | None:
    response: Any = getattr(exc, "response", None)
    if response is None:
        return None
    return getattr(response, "status_code", None)
