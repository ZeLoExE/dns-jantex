# Changelog

## 3.0.4 — Stability and security patch

### Security

- Run the main UI without Administrator privileges.
- Add a small UAC-elevated helper restricted to `set`, `reset`, and `flush`.
- Validate helper requests after elevation and reject unknown fields/operations.
- Quote adapter aliases as PowerShell literals and fail on cmdlet errors.
- Require exact Installer/checksum assets, declared size and SHA-256 before
  automatic installation; enforce a pinned Authenticode signer when configured.
- Re-verify SHA-256 (and the optional signer pin) inside the standalone updater.

### Correctness

- Replace ICMP latency checks with real UDP DNS queries and median sampling.
- Honor DNS timeout values and remove bursts of PowerShell ping processes.
- Fix Auto Flush so it runs exactly once only when enabled.
- Persist language and skipped-update state.
- Store the selected provider by stable name rather than mutable list index.
- Select the active adapter by Windows default-route metric.
- Avoid applying a connected but inactive Wi-Fi profile to Ethernet.
- Use canonical IPv4 validation in every input path.
- Remove duplicate provider pairs, fix Level 3 C secondary DNS, and correct the
  Persian Mullvad translation key.
- Rename misleading query/uptime analytics to health checks/monitoring time.

### Reliability

- Move user data to `%LOCALAPPDATA%\DNS Jantex` with legacy migration.
- Write JSON atomically and preserve corrupt files for recovery.
- Replace forced QThread termination with cooperative shutdown.
- Keep worker objects alive until their QThread has stopped.
- Add Windows/Linux CI, Ruff linting, and automated tests.

### Release note

Automatic installation requires `DNSJantex-Setup.exe` plus the generated
`DNSJantex-checksums.json` asset. Size and SHA-256 are checked before execution.
A configured Code Signing Certificate adds mandatory Authenticode pinning.
