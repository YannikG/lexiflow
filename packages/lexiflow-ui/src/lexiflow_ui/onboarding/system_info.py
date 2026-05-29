"""Host system information probes for onboarding."""

from __future__ import annotations

import platform
from typing import Protocol

RECOMMENDED_RAM_BYTES = 8 * 1024**3


class SystemInfo(Protocol):
    def total_ram_bytes(self) -> int: ...


class PlatformSystemInfo:
    def total_ram_bytes(self) -> int:
        if platform.system() == "Darwin":
            try:
                import ctypes
                import ctypes.util

                libc = ctypes.CDLL(ctypes.util.find_library("c"))
                mib = (ctypes.c_int * 2)(6, 24)  # CTL_HW, HW_MEMSIZE
                size = ctypes.c_uint64()
                length = ctypes.c_size_t(ctypes.sizeof(size))
                if (
                    libc.sysctl(
                        mib, 2, ctypes.byref(size), ctypes.byref(length), None, 0
                    )
                    == 0
                ):
                    return int(size.value)
            except OSError:
                pass
        try:
            import os

            return os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES")
        except (AttributeError, OSError, ValueError):
            return 0
