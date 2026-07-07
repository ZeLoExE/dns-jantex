"""
Update checker for DNS Jantex.
Checks GitHub Releases for newer versions.
"""

import json
import re
import sys
import urllib.request
import urllib.error
from dataclasses import dataclass
from pathlib import Path


GITHUB_API_URL = "https://api.github.com/repos/ZeLoExE/dns-jantex/releases/latest"

if getattr(sys, "frozen", False):
    _BUNDLE_DIR = Path(sys._MEIPASS)
else:
    _BUNDLE_DIR = Path(__file__).resolve().parent.parent

CURRENT_VERSION_FILE = _BUNDLE_DIR / "VERSION"


def get_current_version() -> str:
    """Return the current application version."""
    if CURRENT_VERSION_FILE.exists():
        return CURRENT_VERSION_FILE.read_text(encoding="utf-8").strip()
    return "2.4.0"


def _parse_version(version_str: str) -> tuple[int, ...]:
    """Parse a version string like '2.4.0' into a tuple of ints for comparison."""
    cleaned = version_str.strip().lstrip("vV")
    parts = re.split(r"[.\-]", cleaned)
    result = []
    for p in parts:
        if p.isdigit():
            result.append(int(p))
    return tuple(result) if result else (0,)


@dataclass
class UpdateInfo:
    """Information about an available update."""
    version: str
    download_url: str
    release_notes: str
    size_bytes: int = 0


class UpdateChecker:
    """Checks for application updates via GitHub Releases API."""

    def __init__(self):
        self.current_version = get_current_version()

    def check_for_update(self) -> UpdateInfo | None:
        """
        Check GitHub Releases for a newer version.
        Returns UpdateInfo if an update is available, None otherwise.
        Raises on network errors.
        """
        req = urllib.request.Request(
            GITHUB_API_URL,
            headers={
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "DNS-Jantex-Updater",
            },
        )

        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        latest_version = data.get("tag_name", "")
        if not latest_version:
            return None

        # Compare versions
        if _parse_version(latest_version) <= _parse_version(self.current_version):
            return None

        # Find the installer asset
        download_url = ""
        size_bytes = 0
        for asset in data.get("assets", []):
            name = asset.get("name", "")
            if name.lower().endswith(".exe") and "setup" in name.lower():
                download_url = asset.get("browser_download_url", "")
                size_bytes = asset.get("size", 0)
                break

        if not download_url:
            # Fallback: find any .exe asset
            for asset in data.get("assets", []):
                if asset.get("name", "").lower().endswith(".exe"):
                    download_url = asset.get("browser_download_url", "")
                    size_bytes = asset.get("size", 0)
                    break

        if not download_url:
            return None

        return UpdateInfo(
            version=latest_version,
            download_url=download_url,
            release_notes=data.get("body", ""),
            size_bytes=size_bytes,
        )


def download_file(url: str, dest: Path, progress_callback=None) -> bool:
    """
    Download a file from url to dest.
    Calls progress_callback(bytes_downloaded, total_bytes) periodically.
    Returns True on success.
    """
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "DNS-Jantex-Updater"},
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            total = int(resp.headers.get("Content-Length", 0))
            downloaded = 0
            chunk_size = 65536

            with open(dest, "wb") as f:
                while True:
                    chunk = resp.read(chunk_size)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    if progress_callback:
                        progress_callback(downloaded, total)

        return True
    except Exception:
        # Clean up partial file on failure
        if dest.exists():
            dest.unlink()
        return False
