"""Bridge Hugging Face Hub tqdm progress to LexiFlow callbacks."""

from __future__ import annotations

import io
from collections.abc import Callable

from huggingface_hub.utils.tqdm import tqdm as hf_tqdm


class ReportingTqdm(hf_tqdm):
    """tqdm subclass that reports fractional progress and a console line."""

    def __init__(
        self,
        *args: object,
        on_fraction: Callable[[float], None] | None = None,
        on_log_line: Callable[[str], None] | None = None,
        **kwargs: object,
    ) -> None:
        self._on_fraction = on_fraction
        self._on_log_line = on_log_line
        kwargs.setdefault("file", io.StringIO())
        super().__init__(*args, **kwargs)  # type: ignore[no-untyped-call]

    def display(self, msg: str | None = None, pos: int | None = None) -> bool:
        super().display(msg=msg, pos=pos)
        self._emit_status()
        return True

    def update(self, n: float = 1) -> bool:
        result = bool(super().update(n))
        self._emit_status()
        return result

    def _emit_status(self) -> None:
        text = str(self).strip()
        if self._on_log_line is not None and text:
            self._on_log_line(text)
        if self._on_fraction is not None and self.total:
            total = float(self.total)
            if total > 0:
                self._on_fraction(min(1.0, float(self.n) / total))


def reporting_tqdm_factory(
    *,
    on_fraction: Callable[[float], None] | None = None,
    on_log_line: Callable[[str], None] | None = None,
) -> type[ReportingTqdm]:
    """Return a tqdm class wired to the given callbacks for snapshot_download."""

    class _FactoryTqdm(ReportingTqdm):
        def __init__(self, *args: object, **kwargs: object) -> None:
            super().__init__(
                *args,
                on_fraction=on_fraction,
                on_log_line=on_log_line,
                **kwargs,
            )

    return _FactoryTqdm
