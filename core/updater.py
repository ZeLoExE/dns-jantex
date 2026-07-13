"""Verified GitHub release updater with SHA-256 and optional Authenticode pinning."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, replace
from pathlib import Path

from .paths import bundle_dir
from .powershell import PowerShellExecutor, quote_ps_literal

GITHUB_API_URL = "https://api.github.com/repos/ZeLoExE/dns-jantex/releases/latest"
RELEASES_URL = "https://github.com/ZeLoExE/dns-jantex/releases/latest"
INSTALLER_ASSET_NAME = "DNSJantex-Setup.exe"
CHECKSUM_ASSET_NAME = "DNSJantex-checksums.json"
MAX_INSTALLER_SIZE = 250 * 1024 * 1024
MAX_MANIFEST_SIZE = 64 * 1024
ALLOWED_DOWNLOAD_HOSTS = frozenset({
    "github.com",
    "objects.githubusercontent.com",
    "release-assets.githubusercontent.com",
})
CURRENT_VERSION_FILE = bundle_dir() / "VERSION"
SIGNING_IDENTITY_FILE = bundle_dir() / "SIGNING_CERTIFICATE.txt"


def get_current_version() -> str:
    if CURRENT_VERSION_FILE.exists():
        return CURRENT_VERSION_FILE.read_text(encoding="utf-8").strip()
    return "0.0.0"


def _parse_version(version_str: str) -> tuple[int, ...]:
    cleaned = version_str.strip().lstrip("vV")
    match = re.match(r"^(\d+(?:\.\d+)*)", cleaned)
    if not match:
        return (0, 0, 0)
    parts = [int(part) for part in match.group(1).split(".")]
    return tuple((parts + [0, 0, 0])[:3])


def _allowed_download_url(url: str) -> bool:
    parsed = urllib.parse.urlparse(url)
    return parsed.scheme == "https" and (parsed.hostname or "").lower() in ALLOWED_DOWNLOAD_HOSTS


def _matching_asset(data: dict, name: str) -> dict | None:
    matches = [
        asset for asset in data.get("assets", [])
        if isinstance(asset, dict) and asset.get("name") == name
    ]
    return matches[0] if len(matches) == 1 else None


@dataclass(frozen=True)
class UpdateInfo:
    version: str
    download_url: str
    release_notes: str
    size_bytes: int = 0
    release_url: str = RELEASES_URL
    asset_name: str = INSTALLER_ASSET_NAME
    checksum_url: str = ""
    sha256: str = ""


def _parse_release_data(data: dict, current_version: str) -> UpdateInfo | None:
    latest_version = data.get("tag_name", "")
    if not isinstance(latest_version, str) or not latest_version:
        return None
    if _parse_version(latest_version) <= _parse_version(current_version):
        return None

    installer = _matching_asset(data, INSTALLER_ASSET_NAME)
    checksum = _matching_asset(data, CHECKSUM_ASSET_NAME)
    if installer is None or checksum is None:
        return None

    download_url = installer.get("browser_download_url", "")
    checksum_url = checksum.get("browser_download_url", "")
    size = installer.get("size", 0)
    checksum_size = checksum.get("size", 0)
    if not isinstance(download_url, str) or not _allowed_download_url(download_url):
        return None
    if not isinstance(checksum_url, str) or not _allowed_download_url(checksum_url):
        return None
    if not isinstance(size, int) or size <= 0 or size > MAX_INSTALLER_SIZE:
        return None
    if not isinstance(checksum_size, int) or checksum_size <= 0 or checksum_size > MAX_MANIFEST_SIZE:
        return None

    release_url = data.get("html_url", RELEASES_URL)
    if not isinstance(release_url, str) or not _allowed_download_url(release_url):
        release_url = RELEASES_URL
    notes = data.get("body", "")
    if not isinstance(notes, str):
        notes = ""
    return UpdateInfo(
        version=latest_version,
        download_url=download_url,
        release_notes=notes,
        size_bytes=size,
        release_url=release_url,
        checksum_url=checksum_url,
    )


def _parse_checksum_manifest(data: object, info: UpdateInfo) -> str:
    if not isinstance(data, dict):
        raise ValueError("Invalid checksum manifest")
    version = data.get("version", "")
    if not isinstance(version, str) or _parse_version(version) != _parse_version(info.version):
        raise ValueError("Checksum manifest version does not match release")
    assets = data.get("assets")
    if not isinstance(assets, dict) or set(assets) != {INSTALLER_ASSET_NAME}:
        raise ValueError("Checksum manifest contains unexpected assets")
    entry = assets[INSTALLER_ASSET_NAME]
    if not isinstance(entry, dict):
        raise ValueError("Invalid installer checksum entry")
    size = entry.get("size")
    sha256 = str(entry.get("sha256", "")).lower()
    if size != info.size_bytes:
        raise ValueError("Checksum manifest size does not match release metadata")
    if not re.fullmatch(r"[0-9a-f]{64}", sha256):
        raise ValueError("Invalid installer SHA-256")
    return sha256


def _fetch_json_asset(url: str, maximum_bytes: int) -> object:
    if not _allowed_download_url(url):
        raise ValueError("Untrusted release asset URL")
    request = urllib.request.Request(url, headers={"User-Agent": "DNS-Jantex-Updater"})
    with urllib.request.urlopen(request, timeout=15) as response:
        if not _allowed_download_url(response.geturl()):
            raise ValueError("Release asset redirected to an untrusted host")
        payload = response.read(maximum_bytes + 1)
    if len(payload) > maximum_bytes:
        raise ValueError("Release asset is too large")
    return json.loads(payload.decode("utf-8"))


class UpdateChecker:
    def __init__(self):
        self.current_version = get_current_version()

    def check_for_update(self) -> UpdateInfo | None:
        request = urllib.request.Request(
            GITHUB_API_URL,
            headers={
                "Accept": "application/vnd.github+json",
                "User-Agent": "DNS-Jantex-Updater",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )
        with urllib.request.urlopen(request, timeout=15) as response:
            if response.geturl() != GITHUB_API_URL:
                raise ValueError("Unexpected update API redirect")
            data = json.loads(response.read(2 * 1024 * 1024).decode("utf-8"))
        if not isinstance(data, dict):
            raise ValueError("Invalid GitHub release response")

        info = _parse_release_data(data, self.current_version)
        if info is None:
            latest = data.get("tag_name", "")
            if isinstance(latest, str) and _parse_version(latest) > _parse_version(self.current_version):
                raise ValueError("New release is missing verified update assets")
            return None
        manifest = _fetch_json_asset(info.checksum_url, MAX_MANIFEST_SIZE)
        return replace(info, sha256=_parse_checksum_manifest(manifest, info))


def download_file(url: str, dest: Path, progress_callback=None, *,
                  expected_size: int = 0, expected_sha256: str = "") -> bool:
    """Download one allow-listed installer atomically and verify size + SHA-256."""
    expected_sha256 = expected_sha256.lower()
    if not _allowed_download_url(url):
        return False
    if expected_size <= 0 or expected_size > MAX_INSTALLER_SIZE:
        return False
    if not re.fullmatch(r"[0-9a-f]{64}", expected_sha256):
        return False

    request = urllib.request.Request(url, headers={"User-Agent": "DNS-Jantex-Updater"})
    partial = dest.with_suffix(dest.suffix + ".part")
    downloaded = 0
    digest = hashlib.sha256()
    try:
        dest.parent.mkdir(parents=True, exist_ok=True)
        with urllib.request.urlopen(request, timeout=30) as response:
            if not _allowed_download_url(response.geturl()):
                raise ValueError("Download redirected to an untrusted host")
            declared = int(response.headers.get("Content-Length", 0) or 0)
            if declared and declared != expected_size:
                raise ValueError("Installer size does not match release metadata")
            with partial.open("wb") as handle:
                while True:
                    chunk = response.read(65536)
                    if not chunk:
                        break
                    downloaded += len(chunk)
                    if downloaded > expected_size or downloaded > MAX_INSTALLER_SIZE:
                        raise ValueError("Installer exceeded expected size")
                    digest.update(chunk)
                    handle.write(chunk)
                    if progress_callback:
                        progress_callback(downloaded, expected_size)
                handle.flush()
                os.fsync(handle.fileno())
        if downloaded != expected_size:
            raise ValueError("Installer download is incomplete")
        if not hmac.compare_digest(digest.hexdigest(), expected_sha256):
            raise ValueError("Installer SHA-256 does not match release manifest")
        os.replace(partial, dest)
        return True
    except (OSError, ValueError, urllib.error.URLError):
        for path in (partial, dest):
            try:
                path.unlink(missing_ok=True)
            except OSError:
                pass
        return False


def configured_signer_thumbprint() -> str | None:
    """Read the optional pinned Authenticode certificate thumbprint."""
    try:
        lines = SIGNING_IDENTITY_FILE.read_text(encoding="utf-8").splitlines()
    except OSError:
        return None
    for line in lines:
        candidate = re.sub(r"[^0-9A-Fa-f]", "", line.split("#", 1)[0])
        if len(candidate) == 40:
            return candidate.upper()
    return None


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_installer_signature(path: Path) -> tuple[bool, str]:
    """Require a valid Authenticode signature from the configured certificate."""
    expected = configured_signer_thumbprint()
    if not expected:
        return False, "No signing certificate is configured"
    if sys.platform != "win32" or not path.is_file():
        return False, "Installer signature verification is unavailable"

    literal = quote_ps_literal(str(path.resolve()))
    command = (
        f"$sig = Get-AuthenticodeSignature -LiteralPath {literal}; "
        "$thumb = if ($sig.SignerCertificate) { $sig.SignerCertificate.Thumbprint } else { '' }; "
        "$subject = if ($sig.SignerCertificate) { $sig.SignerCertificate.Subject } else { '' }; "
        "[PSCustomObject]@{ Status = [string]$sig.Status; Thumbprint = $thumb; Subject = $subject } "
        "| ConvertTo-Json -Compress"
    )
    success, data = PowerShellExecutor.execute_json(command, timeout=30)
    if not success or not isinstance(data, dict):
        return False, "Could not verify installer signature"
    status = str(data.get("Status", ""))
    actual = re.sub(r"[^0-9A-Fa-f]", "", str(data.get("Thumbprint", ""))).upper()
    if status != "Valid":
        return False, f"Installer signature status is {status or 'unknown'}"
    if actual != expected:
        return False, "Installer signer does not match the pinned DNS Jantex certificate"
    return True, "Authenticode signer verified"


def verify_installer_package(path: Path, expected_sha256: str) -> tuple[bool, str]:
    """Re-check the downloaded file; require Authenticode too when configured."""
    expected_sha256 = expected_sha256.lower()
    if not path.is_file() or not re.fullmatch(r"[0-9a-f]{64}", expected_sha256):
        return False, "Invalid installer verification data"
    try:
        actual = file_sha256(path)
    except OSError:
        return False, "Could not read downloaded installer"
    if not hmac.compare_digest(actual, expected_sha256):
        return False, "Installer SHA-256 verification failed"

    if configured_signer_thumbprint():
        signature_ok, message = verify_installer_signature(path)
        if not signature_ok:
            return False, message
        return True, f"SHA-256 and {message}"
    return True, f"SHA-256 verified ({actual[:12]}…)"
