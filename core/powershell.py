"""Constrained PowerShell execution helpers used by trusted application code."""

from __future__ import annotations

import ctypes
import json
import logging
import os
import re
import subprocess
from typing import Optional

logger = logging.getLogger(__name__)
DEBUG_PERF = os.environ.get("DNS_JANTEX_DEBUG_PERF", "").lower() in {"1", "true", "yes"}
CREATE_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def quote_ps_literal(value: str) -> str:
    """Quote untrusted text as a PowerShell single-quoted literal."""
    if not isinstance(value, str):
        raise TypeError("PowerShell literal must be a string")
    return "'" + value.replace("'", "''") + "'"


class PowerShellExecutor:
    """Execute fixed PowerShell scripts without a profile or policy bypass."""

    @staticmethod
    def is_admin() -> bool:
        try:
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except (AttributeError, OSError):
            return False

    @staticmethod
    def execute(command: str, timeout: int = 30) -> tuple[bool, str]:
        """Run trusted script text and return ``(success, output_or_error)``.

        Callers must quote every external value with :func:`quote_ps_literal`.
        The wrapper turns non-terminating cmdlet errors into a non-zero exit.
        """
        import time

        started = time.perf_counter()
        wrapped = (
            "& { [Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false); "
            "$ErrorActionPreference = 'Stop'; try { " + command + " } "
            "catch { [Console]::Error.WriteLine($_.Exception.Message); exit 1 } }"
        )
        args = [
            "powershell.exe",
            "-NoLogo",
            "-NoProfile",
            "-NonInteractive",
            "-Command",
            wrapped,
        ]
        try:
            result = subprocess.run(
                args,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout,
                creationflags=CREATE_NO_WINDOW,
            )
        except subprocess.TimeoutExpired:
            return False, "Command timed out"
        except FileNotFoundError:
            return False, "PowerShell not found"
        except OSError as exc:
            return False, f"OS error: {exc}"

        if DEBUG_PERF:
            elapsed = (time.perf_counter() - started) * 1000
            logger.debug("PowerShell (%.0fms): %s", elapsed, command[:80].replace("\n", " "))

        stdout = result.stdout.strip()
        stderr = result.stderr.strip()
        if result.returncode != 0:
            return False, stderr or stdout or f"PowerShell exited with {result.returncode}"
        if stderr:
            logger.warning("PowerShell warning: %s", stderr)
        return True, stdout

    @staticmethod
    def execute_json(command: str, timeout: int = 30) -> tuple[bool, Optional[object]]:
        success, output = PowerShellExecutor.execute(command, timeout)
        if not success or not output:
            return success, output if not success else None
        try:
            return True, json.loads(output)
        except json.JSONDecodeError:
            if output.startswith("@{"):
                return True, PowerShellExecutor._parse_ps_hashtable(output)
            return True, output

    @staticmethod
    def _parse_ps_hashtable(text: str) -> dict:
        result = {}
        inner = text.strip().lstrip("@{").rstrip("}")
        for part in re.split(r";\s*", inner):
            if "=" in part:
                key, _, value = part.partition("=")
                result[key.strip()] = value.strip().strip('"').strip("'")
        return result
