# Release signing

DNS Jantex always verifies the exact release asset name, declared size and
SHA-256 from `DNSJantex-checksums.json`. Authenticode pinning is an optional
second layer that becomes mandatory automatically when a certificate thumbprint
is configured in the build.

## Configure a signed production build

1. Obtain a trusted Authenticode code-signing certificate.
2. Put its 40-character SHA-1 certificate thumbprint (certificate identity, not
   a file hash) in `SIGNING_CERTIFICATE.txt` before building.
3. Build the application binaries.
4. Sign `DNSChanger.exe`, `Updater.exe`, `DNSHelper.exe` and the final
   `DNSJantex-Setup.exe` with `signtool` and an RFC 3161 timestamp.
5. Generate `DNSJantex-checksums.json` only **after** signing the Installer.
6. Verify on a clean Windows VM:

```powershell
Get-AuthenticodeSignature .\DNSJantex-Setup.exe | Format-List *
```

When a thumbprint is embedded, the updater requires both a matching SHA-256 and
a valid Authenticode signature from exactly that certificate. If the pin is
absent, SHA-256 verification remains required and Auto Update continues without
the signature layer.

Never commit a PFX or its password. Store those values only in GitHub Actions
Secrets when signing is added to the release workflow.
