"""Open Hugging Face pages in the system browser."""

from __future__ import annotations

from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices


def open_url(url: str) -> bool:
    """Open *url* in the default browser. Returns whether launch was attempted."""
    return QDesktopServices.openUrl(QUrl(url))
