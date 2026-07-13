"""Application data paths and one-time migration helpers."""

from __future__ import annotations

import ctypes
import os
import shutil
import sys
import uuid
from pathlib import Path

APP_DIR_NAME = "DNS Jantex"


def bundle_dir() -> Path:
    """Return the read-only resource directory for source and frozen builds."""
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent.parent


def executable_dir() -> Path:
    """Return the directory containing the executable or source tree."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def _known_folder_local_app_data() -> Path | None:
    """Resolve LocalAppData through Windows, not an attacker-controlled env var."""
    if sys.platform != "win32":
        return None

    class GUID(ctypes.Structure):
        _fields_ = [
            ("Data1", ctypes.c_uint32),
            ("Data2", ctypes.c_uint16),
            ("Data3", ctypes.c_uint16),
            ("Data4", ctypes.c_ubyte * 8),
        ]

    raw = uuid.UUID("F1B32785-6FBA-4FCF-9D55-7B8E7F157091").bytes_le
    folder_id = GUID.from_buffer_copy(raw)
    output = ctypes.c_wchar_p()
    try:
        shell32 = ctypes.WinDLL("shell32", use_last_error=True)
        ole32 = ctypes.WinDLL("ole32", use_last_error=True)
        shell32.SHGetKnownFolderPath.argtypes = [
            ctypes.POINTER(GUID), ctypes.c_uint32, ctypes.c_void_p,
            ctypes.POINTER(ctypes.c_wchar_p),
        ]
        shell32.SHGetKnownFolderPath.restype = ctypes.c_long
        ole32.CoTaskMemFree.argtypes = [ctypes.c_void_p]
        ole32.CoTaskMemFree.restype = None
        result = shell32.SHGetKnownFolderPath(
            ctypes.byref(folder_id), 0, None, ctypes.byref(output)
        )
        if result != 0 or not output.value:
            return None
        return Path(output.value)
    except (AttributeError, OSError):
        return None
    finally:
        if output.value:
            try:
                ole32.CoTaskMemFree(ctypes.cast(output, ctypes.c_void_p))
            except (AttributeError, NameError, OSError):
                pass


def data_dir() -> Path:
    """Return a per-user writable data directory.

    DNS_JANTEX_DATA_DIR is available only to source/development builds. Frozen
    production helpers ignore it so elevation cannot be abused for file writes.
    """
    override = os.environ.get("DNS_JANTEX_DATA_DIR")
    if override and not getattr(sys, "frozen", False):
        return Path(override).expanduser().resolve()

    known_folder = _known_folder_local_app_data()
    if known_folder:
        return known_folder / APP_DIR_NAME

    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data and sys.platform != "win32":
        return Path(local_app_data) / APP_DIR_NAME

    return Path.home() / ".dns-jantex"


def ensure_data_dir() -> Path:
    path = data_dir()
    path.mkdir(parents=True, exist_ok=True)
    return path


def ipc_dir() -> Path:
    path = ensure_data_dir() / "ipc"
    path.mkdir(parents=True, exist_ok=True)
    return path


def migrate_legacy_config() -> None:
    """Copy legacy Program Files/source config into the per-user data folder.

    Existing destination files always win. A marker makes this operation
    idempotent; legacy files are kept so users can roll back safely.
    """
    destination = ensure_data_dir()
    marker = destination / ".legacy-config-migrated"
    if marker.exists():
        return

    legacy = executable_dir() / "config"
    if legacy.exists() and legacy.resolve() != destination.resolve():
        for name in ("settings.json", "custom_dns.json", "network_profiles.json"):
            src = legacy / name
            dst = destination / name
            if src.is_file() and not dst.exists():
                try:
                    shutil.copy2(src, dst)
                except OSError:
                    # A failed file is retried on the next launch.
                    return

    try:
        marker.write_text("3.0.4\n", encoding="utf-8")
    except OSError:
        pass
