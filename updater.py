"""
DNS Jantex Updater - Standalone updater executable.

Usage:
    updater.exe <installer_path> <app_exe_name>

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


def run_installer(installer_path: Path) -> bool:
    """Run the NSIS installer silently and wait for it to finish."""
    if not installer_path.exists():
        return False

    # NSIS supports /S for silent install
    proc = subprocess.Popen(
        [str(installer_path), "/S"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
    proc.wait(timeout=300)
    return proc.returncode == 0


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
    """Remove the temporary installer file."""
    try:
        if installer_path.exists():
            installer_path.unlink()
    except Exception:
        pass


def main():
    if len(sys.argv) < 3:
        sys.exit(1)

    installer_path = Path(sys.argv[1])
    app_exe_name = sys.argv[2]  # e.g. "DNSChanger.exe"

    # Step 1: Wait for the main application to fully exit
    wait_for_process_exit(app_exe_name, timeout=60)

    # Step 2: Run the installer silently
    if not run_installer(installer_path):
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
