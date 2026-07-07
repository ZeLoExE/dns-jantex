"""Lightweight profiling utilities for DNS Changer.

Usage:
    from core.profiler import timer
    with timer("DNSManager.set_dns"):
        do_work()

    # Or measure a function call:
    result = timer.measure("adapter_lookup", some_function, arg1, arg2)

All timings are printed to stderr and appended to an internal log
accessible via profiler_log().
"""

import time
import sys
import os
from contextlib import contextmanager
from typing import Any, Callable

_LOG: list[tuple[str, float]] = []
_ENABLED = True


def _log(label: str, elapsed_ms: float):
    _LOG.append((label, elapsed_ms))
    if _ENABLED:
        print(f"[PROFILER] {label}: {elapsed_ms:.1f}ms", file=sys.stderr, flush=True)


@contextmanager
def timer(label: str):
    """Context manager that times a block and logs the result."""
    start = time.perf_counter()
    try:
        yield
    finally:
        elapsed_ms = (time.perf_counter() - start) * 1000
        _log(label, elapsed_ms)


def measure(label: str, fn: Callable, *args, **kwargs) -> Any:
    """Call *fn*, measure its wall time, log it, and return the result."""
    start = time.perf_counter()
    result = fn(*args, **kwargs)
    elapsed_ms = (time.perf_counter() - start) * 1000
    _log(label, elapsed_ms)
    return result


def profiler_log() -> list[tuple[str, float]]:
    """Return a copy of all recorded timings."""
    return list(_LOG)


def profiler_summary() -> str:
    """Return a human-readable summary of all recorded timings."""
    if not _LOG:
        return "(no profiling data recorded)"
    lines = ["--- Profiling Summary ---"]
    for label, ms in _LOG:
        lines.append(f"  {label}: {ms:.1f}ms")
    lines.append(f"--- Total entries: {len(_LOG)} ---")
    return "\n".join(lines)


def save_log(path: str | None = None):
    """Write the profiling log to a file."""
    if path is None:
        path = os.path.join(os.environ.get("TEMP", "."), "dns_jantex_profiler.log")
    with open(path, "w", encoding="utf-8") as f:
        f.write(profiler_summary())
    return path
