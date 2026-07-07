"""
Update checker for DNS Jantex.
Checks GitHub Releases for newer versions.
"""

import json
import os
import re
import sys
import traceback
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

# --- Debug logging ---
_LOG_PATH = os.path.join(os.environ.get("TEMP", "."), "update_debug.log")


def _log(msg: str):
    """Append a timestamped line to the debug log and print to stderr."""
    import datetime
    ts = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
    line = f"[{ts}] {msg}"
    try:
        with open(_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass
    print(line, file=sys.stderr, flush=True)


def get_current_version() -> str:
    """Return the current application version."""
    if CURRENT_VERSION_FILE.exists():
        ver = CURRENT_VERSION_FILE.read_text(encoding="utf-8").strip()
        _log(f"get_current_version: VERSION file={CURRENT_VERSION_FILE} content='{ver}'")
        return ver
    _log(f"get_current_version: VERSION file NOT FOUND at {CURRENT_VERSION_FILE}, using default")
    return "2.4.0"


def _parse_version(version_str: str) -> tuple[int, ...]:
    """Parse a version string like '2.4.0' into a tuple of ints for comparison."""
    cleaned = version_str.strip().lstrip("vV")
    parts = re.split(r"[.\-]", cleaned)
    result = []
    for p in parts:
        if p.isdigit():
            result.append(int(p))
    parsed = tuple(result) if result else (0,)
    _log(f"  _parse_version('{version_str}') -> cleaned='{cleaned}' -> parts={parts} -> {parsed}")
    return parsed


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
        _log("check_for_update: START")
        _log(f"  URL: {GITHUB_API_URL}")
        _log(f"  Current version: '{self.current_version}'")

        req = urllib.request.Request(
            GITHUB_API_URL,
            headers={
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "DNS-Jantex-Updater",
            },
        )

        try:
            _log("  Sending HTTP request...")
            resp = urllib.request.urlopen(req, timeout=15)
            _log(f"  HTTP status: {resp.status}")
            raw = resp.read().decode("utf-8")
            _log(f"  Raw response length: {len(raw)} chars")
            _log(f"  Raw response (first 500): {raw[:500]}")
            data = json.loads(raw)
            resp.close()
        except Exception as e:
            _log(f"  HTTP ERROR: {e}")
            _log(f"  Traceback:\n{traceback.format_exc()}")
            raise

        latest_version = data.get("tag_name", "")
        _log(f"  tag_name from API: '{latest_version}'")

        if not latest_version:
            _log("  tag_name is empty, returning None")
            return None

        parsed_latest = _parse_version(latest_version)
        parsed_current = _parse_version(self.current_version)
        is_newer = parsed_latest > parsed_current
        _log(f"  Version comparison: {parsed_latest} > {parsed_current} = {is_newer}")

        if not is_newer:
            _log("  NOT newer, returning None")
            return None

        _log("  Update IS available!")

        # Find the installer asset
        assets = data.get("assets", [])
        _log(f"  Assets count: {len(assets)}")
        for i, asset in enumerate(assets):
            _log(f"    asset[{i}]: name='{asset.get('name')}' size={asset.get('size')} url={asset.get('browser_download_url', '')[:80]}")

        download_url = ""
        size_bytes = 0
        for asset in assets:
            name = asset.get("name", "")
            if name.lower().endswith(".exe") and "setup" in name.lower():
                download_url = asset.get("browser_download_url", "")
                size_bytes = asset.get("size", 0)
                _log(f"  Selected setup asset: '{name}' ({size_bytes} bytes)")
                break

        if not download_url:
            _log("  No setup .exe found, trying fallback...")
            for asset in assets:
                if asset.get("name", "").lower().endswith(".exe"):
                    download_url = asset.get("browser_download_url", "")
                    size_bytes = asset.get("size", 0)
                    _log(f"  Fallback asset: '{asset.get('name')}'")
                    break

        if not download_url:
            _log("  No download URL at all, returning None")
            return None

        info = UpdateInfo(
            version=latest_version,
            download_url=download_url,
            release_notes=data.get("body", ""),
            size_bytes=size_bytes,
        )
        _log(f"  Returning UpdateInfo(version='{info.version}', url='{info.download_url[:60]}...')")
        return info


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
