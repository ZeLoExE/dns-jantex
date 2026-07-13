import hashlib
import io

import pytest

from core.powershell import PowerShellExecutor
from core.updater import (
    CHECKSUM_ASSET_NAME,
    INSTALLER_ASSET_NAME,
    _allowed_download_url,
    _parse_checksum_manifest,
    _parse_release_data,
    _parse_version,
    download_file,
    verify_installer_package,
    verify_installer_signature,
)


def _release(
    name=INSTALLER_ASSET_NAME,
    url="https://github.com/ZeLoExE/dns-jantex/releases/download/v9.0.0/DNSJantex-Setup.exe",
):
    return {
        "tag_name": "v9.0.0",
        "html_url": "https://github.com/ZeLoExE/dns-jantex/releases/tag/v9.0.0",
        "body": "notes",
        "assets": [
            {"name": name, "browser_download_url": url, "size": 12345},
            {
                "name": CHECKSUM_ASSET_NAME,
                "browser_download_url": (
                    "https://github.com/ZeLoExE/dns-jantex/releases/download/"
                    "v9.0.0/DNSJantex-checksums.json"
                ),
                "size": 180,
            },
        ],
    }


def test_version_parser():
    assert _parse_version("v3.0.4") == (3, 0, 4)
    assert _parse_version("3.1.0-beta.1") == (3, 1, 0)
    assert _parse_version("invalid") == (0, 0, 0)


def test_release_requires_exact_installer_checksum_and_trusted_urls():
    assert _parse_release_data(_release(), "3.0.4") is not None
    assert _parse_release_data(_release(name="other.exe"), "3.0.4") is None
    assert _parse_release_data(_release(url="https://evil.example/setup.exe"), "3.0.4") is None

    missing_checksum = _release()
    missing_checksum["assets"] = missing_checksum["assets"][:1]
    assert _parse_release_data(missing_checksum, "3.0.4") is None

    duplicate = _release()
    duplicate["assets"].append(dict(duplicate["assets"][0]))
    assert _parse_release_data(duplicate, "3.0.4") is None


def test_checksum_manifest_is_version_size_and_asset_bound():
    info = _parse_release_data(_release(), "3.0.4")
    digest = "a" * 64
    manifest = {
        "version": "v9.0.0",
        "assets": {INSTALLER_ASSET_NAME: {"size": 12345, "sha256": digest}},
    }
    assert _parse_checksum_manifest(manifest, info) == digest

    manifest["assets"][INSTALLER_ASSET_NAME]["size"] = 12346
    with pytest.raises(ValueError):
        _parse_checksum_manifest(manifest, info)


def test_download_allowlist_is_https_only():
    assert _allowed_download_url("https://github.com/ZeLoExE/dns-jantex/releases/latest")
    assert not _allowed_download_url("http://github.com/example.exe")
    assert not _allowed_download_url("https://github.com.evil.example/example.exe")


def test_download_rejects_hash_mismatch(tmp_path, monkeypatch):
    payload = b"verified installer bytes"

    class FakeResponse(io.BytesIO):
        headers = {"Content-Length": str(len(payload))}

        def geturl(self):
            return "https://release-assets.githubusercontent.com/fixture"

        def __enter__(self):
            return self

        def __exit__(self, *args):
            self.close()

    monkeypatch.setattr(
        "core.updater.urllib.request.urlopen",
        lambda request, timeout=30: FakeResponse(payload),
    )
    destination = tmp_path / INSTALLER_ASSET_NAME
    url = "https://github.com/ZeLoExE/dns-jantex/releases/download/v9.0.0/DNSJantex-Setup.exe"
    expected = hashlib.sha256(payload).hexdigest()
    assert download_file(url, destination, expected_size=len(payload), expected_sha256=expected)
    assert destination.read_bytes() == payload

    destination.unlink()
    assert not download_file(url, destination, expected_size=len(payload), expected_sha256="0" * 64)
    assert not destination.exists()


def test_sha256_package_verification_without_certificate(tmp_path, monkeypatch):
    installer = tmp_path / INSTALLER_ASSET_NAME
    installer.write_bytes(b"checksum-fixture")
    identity = tmp_path / "SIGNING_CERTIFICATE.txt"
    identity.write_text("# no certificate\n", encoding="utf-8")
    monkeypatch.setattr("core.updater.SIGNING_IDENTITY_FILE", identity)
    expected = hashlib.sha256(installer.read_bytes()).hexdigest()
    assert verify_installer_package(installer, expected)[0]
    assert not verify_installer_package(installer, "0" * 64)[0]


def test_authenticode_requires_valid_pinned_signer(tmp_path, monkeypatch):
    installer = tmp_path / INSTALLER_ASSET_NAME
    installer.write_bytes(b"signed-fixture")
    identity = tmp_path / "SIGNING_CERTIFICATE.txt"
    identity.write_text("A" * 40, encoding="utf-8")
    monkeypatch.setattr("core.updater.SIGNING_IDENTITY_FILE", identity)
    monkeypatch.setattr("core.updater.sys.platform", "win32")
    monkeypatch.setattr(
        PowerShellExecutor,
        "execute_json",
        staticmethod(lambda command, timeout=30: (
            True,
            {"Status": "Valid", "Thumbprint": "A" * 40, "Subject": "CN=DNS Jantex"},
        )),
    )
    assert verify_installer_signature(installer)[0]

    monkeypatch.setattr(
        PowerShellExecutor,
        "execute_json",
        staticmethod(lambda command, timeout=30: (
            True,
            {"Status": "Valid", "Thumbprint": "B" * 40, "Subject": "CN=Other"},
        )),
    )
    assert not verify_installer_signature(installer)[0]
