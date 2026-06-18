"""Compare installed version against latest GitHub release."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Protocol
from urllib.error import URLError
from urllib.request import Request, urlopen

import lexiflow_core
from lexiflow_core.version_compare import is_newer_version


@dataclass(frozen=True)
class ReleaseInfo:
    version: str
    download_url: str


class ReleaseClient(Protocol):
    def fetch_latest(self, repo: str) -> ReleaseInfo | None: ...


class GitHubReleaseClient:
    def fetch_latest(self, repo: str) -> ReleaseInfo | None:
        request = Request(
            f"https://api.github.com/repos/{repo}/releases/latest",
            headers={
                "Accept": "application/vnd.github+json",
                "User-Agent": "LexiFlow",
            },
        )
        try:
            with urlopen(request, timeout=5) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (URLError, OSError, json.JSONDecodeError):
            return None
        tag = payload.get("tag_name")
        if not isinstance(tag, str):
            return None
        version = tag.lstrip("v")
        html_url = payload.get("html_url")
        if not isinstance(html_url, str):
            return None
        return ReleaseInfo(version=version, download_url=html_url)


def check_for_app_update(
    *,
    client: ReleaseClient,
    repo: str = "YannikG/lexiflow",
    installed_version: str | None = None,
) -> ReleaseInfo | None:
    """Return release info when a newer GitHub release exists."""
    if installed_version is not None:
        installed = installed_version
    else:
        installed = lexiflow_core.__version__
    latest = client.fetch_latest(repo)
    if latest is None:
        return None
    if is_newer_version(installed, latest.version):
        return latest
    return None
