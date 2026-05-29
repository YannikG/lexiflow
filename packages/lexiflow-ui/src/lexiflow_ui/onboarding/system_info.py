"""Host system information probes for onboarding."""

from __future__ import annotations

import platform
from typing import Protocol

RECOMMENDED_RAM_BYTES = 8 * 1024**3


class SystemInfo(Protocol):
    def total_ram_bytes(self) -> int: ...


def ram_warning_message(total_ram_bytes: int) -> str | None:
    """Return onboarding RAM warning text, or None when no warning is needed."""
    if total_ram_bytes >= RECOMMENDED_RAM_BYTES:
        return None
    if total_ram_bytes == 0:
        return (
            "Could not detect your system RAM. "
            "LexiFlow recommends at least 8 GiB of RAM for local models. "
            "You can continue anyway."
        )
    gib = total_ram_bytes / (1024**3)
    return (
        f"Your system reports about {gib:.1f} GiB of RAM. "
        "LexiFlow recommends at least 8 GiB for local models. "
        "You can continue anyway."
    )


def _darwin_total_ram_bytes() -> int | None:
    try:
        import ctypes
        import ctypes.util

        libc = ctypes.CDLL(ctypes.util.find_library("c"))
        mib = (ctypes.c_int * 2)(6, 24)  # CTL_HW, HW_MEMSIZE
        size = ctypes.c_uint64()
        length = ctypes.c_size_t(ctypes.sizeof(size))
        if libc.sysctl(mib, 2, ctypes.byref(size), ctypes.byref(length), None, 0) == 0:
            return int(size.value)
    except OSError:
        return None
    return None


def _windows_total_ram_bytes() -> int | None:
    try:
        import ctypes

        class MEMORYSTATUSEX(ctypes.Structure):
            _fields_ = [
                ("dwLength", ctypes.c_ulong),
                ("dwMemoryLoad", ctypes.c_ulong),
                ("ullTotalPhys", ctypes.c_uint64),
                ("ullAvailPhys", ctypes.c_uint64),
                ("ullTotalPageFile", ctypes.c_uint64),
                ("ullAvailPageFile", ctypes.c_uint64),
                ("ullTotalVirtual", ctypes.c_uint64),
                ("ullAvailVirtual", ctypes.c_uint64),
                ("ullAvailExtendedVirtual", ctypes.c_uint64),
            ]

        stat = MEMORYSTATUSEX()
        stat.dwLength = ctypes.sizeof(stat)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat)):
            return int(stat.ullTotalPhys)
    except (AttributeError, OSError, ValueError):
        return None
    return None


def _unix_total_ram_bytes() -> int | None:
    try:
        import os

        return os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES")
    except (AttributeError, OSError, ValueError):
        return None


class PlatformSystemInfo:
    def total_ram_bytes(self) -> int:
        system = platform.system()
        if system == "Darwin":
            total = _darwin_total_ram_bytes()
            if total is not None:
                return total
        elif system == "Windows":
            total = _windows_total_ram_bytes()
            if total is not None:
                return total
        total = _unix_total_ram_bytes()
        return total if total is not None else 0
