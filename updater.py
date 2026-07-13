"""
DNS Jantex Updater - Standalone updater executable.

Usage:
    updater.exe <installer_path> <app_exe_name> <expected_sha256>

Workflow:
    1. Wait for the main application to fully exit.
    2. Run the downloaded installer silently.
    3. Wait for installation to complete.
    4. Launch the updated application.
    5. Clean up temporary files.
    6. Exit.
"""

import os
import sys
import time
import subprocess
import tempfile
from pathlib import Path

from core.elevated_client import _run_elevated
from core.updater import verify_installer_package


def wait_for_process_exit(exe_name: str, timeout: int = 60) -> bool:
    """Wait until a process with the given name is no longer running."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        result = subprocess.run(
            ["tasklist", "/FI", f"IMAGENAME eq {exe_name}", "/NH"],
            capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW,
        )
        if exe_name.lower() not in result.stdout.lower():
            return True
        time.sleep(1)
    return False


def run_installer(installer_path: Path, expected_sha256: str) -> bool:
    """Re-verify, elevate, and wait for the NSIS installer."""
    verified, _ = verify_installer_package(installer_path, expected_sha256)
    if not verified:
        return False

    # The main UI is intentionally unprivileged. ShellExecuteEx displays UAC for
    # the already verified installer and gives us a process handle to wait on.
    success, _ = _run_elevated(installer_path, ["/S"], timeout_seconds=300)
    return success


def find_installed_exe() -> Path | None:
    """Find the installed DNSChanger.exe in common locations."""
    candidates = [
        Path(os.environ.get("PROGRAMFILES", r"C:\Program Files")) / "DNS Jantex" / "DNSChanger.exe",
        Path(os.environ.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)")) / "DNS Jantex" / "DNSChanger.exe",
    ]
    for p in candidates:
        if p.exists():
            return p
    return None


def cleanup(installer_path: Path):
    """Remove the installer and its app-created empty temporary directory."""
    try:
        installer_path.unlink(missing_ok=True)
        parent = installer_path.resolve().parent
        system_temp = Path(tempfile.gettempdir()).resolve()
        if parent.parent == system_temp and parent.name.startswith("dns_jantex_update-"):
            parent.rmdir()
    except OSError:
        pass


def main():
    if len(sys.argv) != 4:
        sys.exit(1)

    installer_path = Path(sys.argv[1])
    app_exe_name = sys.argv[2]  # e.g. "DNSChanger.exe"
    expected_sha256 = sys.argv[3]

    # Step 1: Never replace files while the main application is still running.
    if not wait_for_process_exit(app_exe_name, timeout=60):
        cleanup(installer_path)
        sys.exit(1)

    # Step 2: Run the verified installer silently after a UAC prompt
    if not run_installer(installer_path, expected_sha256):
        cleanup(installer_path)
        sys.exit(1)

    # Step 3: Find and launch the updated application
    app_exe = find_installed_exe()
    if app_exe:
        subprocess.Popen(
            [str(app_exe)],
            creationflags=subprocess.DETACHED_PROCESS,
        )

    # Step 4: Clean up
    cleanup(installer_path)

    sys.exit(0)


if __name__ == "__main__":
    main()
