# Validation report — DNS Jantex 3.0.4

Validation environment: Linux sandbox, Python 3.11.

## Passed

- `python -W error -m compileall -q .`
- `python -m pytest -q` — 21 tests passed
- `python -m ruff check core ui main.py helper.py updater.py tests`
- `git diff --check`
- Python AST parsing for every `.py` file
- JSON parsing for both translation files
- Provider dataset checks for IPv4 validity, duplicate pairs, duplicate names,
  identical primary/secondary values, and missing English/Persian keys
- Unit coverage for PowerShell quoting, helper request allow-listing, Auto Flush,
  DNS packet probing/timeouts, route-metric adapter selection, atomic JSON, exact
  update assets, URL allow-listing, and signer-thumbprint matching

## Requires Windows validation

The following cannot be honestly certified outside Windows and must be tested
with [TESTING.md](TESTING.md), preferably in a disposable VM:

- PowerShell `Get-Net*`/`Set-DnsClientServerAddress` behavior
- UAC cancellation/approval and `ShellExecuteExW` process handling
- PyInstaller builds for the app, updater, and helper
- NSIS install, upgrade, and uninstall
- Real Authenticode signing and timestamp validation
- UI rendering, system tray, DPI scaling, RTL layout, and network switching

## Verified-update behavior

Automatic installation requires the exact Installer and checksum-manifest
assets. Size and SHA-256 are mandatory and the standalone updater checks the
hash again before UAC. `SIGNING_CERTIFICATE.txt` currently has no thumbprint, so
Authenticode pinning is not active; configure and test it before claiming a
signed release.
