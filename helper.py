"""DNS Jantex elevated helper.

This process is intentionally tiny: it accepts only set/reset/flush requests,
validates all input again after elevation, and never accepts PowerShell text or
an adapter name from the caller.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from core.dns_manager import DNSManager
from core.helper_protocol import validate_request
from core.paths import ipc_dir
from core.powershell import PowerShellExecutor
from core.storage import atomic_write_json

MAX_REQUEST_BYTES = 4096


def _safe_ipc_path(value: str, prefix: str) -> Path:
    path = Path(value).resolve()
    parent = ipc_dir().resolve()
    if path.parent != parent or path.suffix.lower() != ".json" or not path.name.startswith(prefix):
        raise ValueError("Invalid helper IPC path")
    return path


def process_request(request_path: Path) -> tuple[bool, str]:
    if not PowerShellExecutor.is_admin():
        return False, "DNS helper requires Administrator permission"
    try:
        if request_path.stat().st_size > MAX_REQUEST_BYTES:
            raise ValueError("DNS request is too large")
        payload = json.loads(request_path.read_text(encoding="utf-8"))
        request = validate_request(payload)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        return False, f"Invalid DNS request: {exc}"

    if request.operation == "set":
        return DNSManager.set_dns(
            request.primary,
            request.secondary,
            flush_cache=request.flush_after,
        )
    if request.operation == "reset":
        return DNSManager.reset_to_dhcp()
    return DNSManager.flush_dns_cache()


def main() -> int:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--request", required=True)
    parser.add_argument("--result", required=True)
    try:
        args = parser.parse_args()
        request_path = _safe_ipc_path(args.request, "request-")
        result_path = _safe_ipc_path(args.result, "result-")
        success, message = process_request(request_path)
        atomic_write_json(result_path, {"success": success, "message": message})
        return 0
    except Exception as exc:
        # Do not write to an unvalidated result path.
        try:
            result_path
        except UnboundLocalError:
            return 2
        try:
            atomic_write_json(result_path, {"success": False, "message": str(exc)})
        except OSError:
            pass
        return 2


if __name__ == "__main__":
    sys.exit(main())
