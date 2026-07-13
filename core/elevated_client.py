"""Unprivileged client for the narrowly scoped elevated DNS helper."""

from __future__ import annotations

import ctypes
import json
import subprocess
import sys
import time
import uuid
from ctypes import wintypes
from pathlib import Path

from .helper_protocol import validate_request
from .paths import executable_dir, ipc_dir
from .storage import atomic_write_json

SEE_MASK_NOCLOSEPROCESS = 0x00000040
WAIT_OBJECT_0 = 0x00000000
WAIT_TIMEOUT = 0x00000102
INFINITE = 0xFFFFFFFF


class SHELLEXECUTEINFOW(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("fMask", wintypes.ULONG),
        ("hwnd", wintypes.HWND),
        ("lpVerb", wintypes.LPCWSTR),
        ("lpFile", wintypes.LPCWSTR),
        ("lpParameters", wintypes.LPCWSTR),
        ("lpDirectory", wintypes.LPCWSTR),
        ("nShow", ctypes.c_int),
        ("hInstApp", wintypes.HINSTANCE),
        ("lpIDList", wintypes.LPVOID),
        ("lpClass", wintypes.LPCWSTR),
        ("hkeyClass", wintypes.HKEY),
        ("dwHotKey", wintypes.DWORD),
        ("hIcon", wintypes.HANDLE),
        ("hProcess", wintypes.HANDLE),
    ]


def _helper_command() -> tuple[Path, list[str]]:
    if getattr(sys, "frozen", False):
        return executable_dir() / "DNSHelper.exe", []
    return Path(sys.executable), [str(executable_dir() / "helper.py")]


def _run_elevated(executable: Path, arguments: list[str], timeout_seconds: int) -> tuple[bool, str]:
    if sys.platform != "win32":
        return False, "Elevated DNS operations are supported on Windows only"
    if not executable.is_file():
        return False, f"DNS helper not found: {executable}"

    parameters = subprocess.list2cmdline(arguments)
    shell32 = ctypes.WinDLL("shell32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    shell32.ShellExecuteExW.argtypes = [ctypes.POINTER(SHELLEXECUTEINFOW)]
    shell32.ShellExecuteExW.restype = wintypes.BOOL
    kernel32.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    kernel32.WaitForSingleObject.restype = wintypes.DWORD
    kernel32.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
    kernel32.GetExitCodeProcess.restype = wintypes.BOOL
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel32.CloseHandle.restype = wintypes.BOOL

    info = SHELLEXECUTEINFOW()
    info.cbSize = ctypes.sizeof(info)
    info.fMask = SEE_MASK_NOCLOSEPROCESS
    info.lpVerb = "runas"
    info.lpFile = str(executable)
    info.lpParameters = parameters
    info.lpDirectory = str(executable.parent)
    info.nShow = 0

    if not shell32.ShellExecuteExW(ctypes.byref(info)):
        error = ctypes.get_last_error()
        if error == 1223:
            return False, "Administrator permission was cancelled"
        return False, f"Could not start DNS helper (Windows error {error})"

    try:
        wait_result = kernel32.WaitForSingleObject(info.hProcess, timeout_seconds * 1000)
        if wait_result == WAIT_TIMEOUT:
            return False, "DNS helper timed out"
        if wait_result != WAIT_OBJECT_0:
            return False, "Could not wait for DNS helper"
        exit_code = wintypes.DWORD()
        if not kernel32.GetExitCodeProcess(info.hProcess, ctypes.byref(exit_code)):
            return False, "Could not read DNS helper result"
        return exit_code.value == 0, f"DNS helper exited with code {exit_code.value}"
    finally:
        kernel32.CloseHandle(info.hProcess)


class ElevatedDNSClient:
    """Execute one allow-listed DNS operation after a standard UAC prompt."""

    @staticmethod
    def execute(operation: str, primary: str = "", secondary: str = "",
                *, flush_after: bool = False, timeout_seconds: int = 75) -> tuple[bool, str]:
        request = validate_request({
            "operation": operation,
            "primary": primary,
            "secondary": secondary,
            "flush_after": flush_after,
        })
        token = uuid.uuid4().hex
        directory = ipc_dir()
        request_path = directory / f"request-{token}.json"
        result_path = directory / f"result-{token}.json"
        atomic_write_json(request_path, request.as_dict())

        executable, prefix = _helper_command()
        arguments = prefix + ["--request", str(request_path), "--result", str(result_path)]
        try:
            started, launch_message = _run_elevated(executable, arguments, timeout_seconds)
            if not started:
                return False, launch_message

            # The process handle is signalled after file handles close; this short retry
            # only accommodates antivirus/filesystem propagation delays.
            for _ in range(20):
                if result_path.exists():
                    break
                time.sleep(0.05)
            if not result_path.exists():
                return False, "DNS helper returned no result"

            try:
                payload = json.loads(result_path.read_text(encoding="utf-8"))
            except (OSError, UnicodeError, json.JSONDecodeError):
                return False, "DNS helper returned an invalid result"
            if not isinstance(payload, dict) or not isinstance(payload.get("success"), bool):
                return False, "DNS helper returned an invalid result"
            message = payload.get("message", "")
            if not isinstance(message, str):
                message = ""
            return payload["success"], message
        finally:
            for path in (request_path, result_path):
                try:
                    path.unlink(missing_ok=True)
                except OSError:
                    pass
