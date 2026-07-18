<p align="center">
  <img src="docs/logo.png" width="100">
</p>

<h1 align="center">DNS Jantex</h1>

<p align="center">
  <img src="https://img.shields.io/badge/version-3.0.4-6366f1?style=for-the-badge" alt="Version">
  <img src="https://img.shields.io/badge/python-3.10+-3776ab?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/platform-Windows_10%2F11-0078d4?style=for-the-badge&logo=windows&logoColor=white" alt="Windows">
  <img src="https://img.shields.io/badge/license-MIT-22c55e?style=for-the-badge" alt="License">
  <a href="https://dns-jantex.vercel.app/"><img src="https://img.shields.io/badge/Website-dns--jantex.vercel.app-blue?style=for-the-badge&logo=googlechrome&logoColor=white" alt="Website"></a>
  <a href="https://dns-jantex.vercel.app/"><img src="https://img.shields.io/badge/Web_App-Live-green?style=for-the-badge&logo=vuedotjs&logoColor=white" alt="Web App"></a>
</p>

<p align="center">
  A modern Windows DNS management app with 45+ IPv4 providers, network profiles, real DNS-query benchmarking, a SHA-256-verified updater, and Persian support.
</p>

---

## Screenshots

<p align="center">
  <img src="docs/screenshot.png" width="700">
  <br>
  <em>Dark mode with preferences menu open</em>
</p>

## Download

Download the latest installer from [Releases](https://github.com/ZeLoExE/dns-jantex/releases).

## Antivirus Result

You can check the antivirus result [here](https://www.virustotal.com/gui/file/4ea6de333a9706ab081336f0cf237b44061e02e00d1ac76c6fdb46515a7f41ee?nocache=1).

## Features

### DNS Management
- **45+ DNS providers** — Google, Cloudflare, Quad9, AdGuard, OpenDNS, Norton, Level3, and many more
- **Smart Connect** — benchmarks real UDP DNS queries (three samples/provider) and selects the lowest median latency
- **Custom DNS presets** — save frequently used manual DNS inputs for quick access
- **Manage DNS modal** — add, edit, and delete custom DNS entries with a unified data store
- **One-click apply** — fast DNS switching with instant confirmation
- **Flush & reset** — clear DNS cache or restore automatic (DHCP) settings
- **Auto-Flush DNS** — optionally flush DNS cache automatically after every Apply

### Network Profiles
- **Profile-based DNS** — create DNS profiles linked to specific Wi-Fi networks or Ethernet adapters
- **Auto-detection** — detect current Wi-Fi SSID or Ethernet adapter name when creating profiles
- **Auto-Switch** — automatically apply the correct DNS profile when connecting to a recognized network
- **Confirmation dialog** — get prompted before applying when Auto-Switch is disabled
- **Profile icons** — assign custom emoji icons to profiles (🏠 Home, 🎓 School, 🎮 Gaming, 🏢 Office)

### Monitoring & Analytics
- **Network Stream graph** — real-time bandwidth monitor showing upload/download speed
- **Ping Stat chart** — line chart tracking latency history over time
- **DNS health analytics** — monitoring time, successful/failed health checks, and latency history
- **Status indicator** — green/yellow/red dot shows DNS health at a glance

### User Experience
- **Toast notifications** — desktop-level notifications that appear at the screen corner, auto-dismiss after 3 seconds
- **Animated dialogs** — smooth fade-in animations on all dialogs and popups
- **Hover effects** — icon color transitions on interactive buttons for better visibility
- **Favorites system** — star your most-used DNS providers to pin them to the top of the list
- **Tag filters** — filter providers by Gaming, Ad Blocking, Family Safe, Privacy, Security, or Anti-Sanction
- **Sticky search bar** — search stays accessible as you scroll through the provider list

### System & Theme
- **System tray** — minimize to tray, double-click to restore, right-click context menu
- **Verified auto-updater** — requires exact release assets, size and SHA-256; optionally enforces a pinned Authenticode signer
- **Dark & light themes** — switch with one click, fully theme-aware UI
- **English & Persian** — Persian translations with RTL layout (remaining dialogs are being migrated)
- **Frameless window** — modern custom title bar with native Windows 11 shadow and rounded corners
- **Installer** — desktop and Start Menu shortcuts included

## Requirements

- Windows 10/11
- Administrator approval is requested only for Apply, Reset, and Flush operations

## Installation

1. Download `DNSJantex-Setup.exe` from [Releases](https://github.com/ZeLoExE/dns-jantex/releases)
2. Run the installer and approve its Windows UAC prompt
3. Follow the setup wizard
4. Launch DNS Jantex normally from Desktop or Start Menu

## Usage

1. Run **DNS Jantex** normally; Windows requests approval only when a DNS change is made
2. Click **Smart Connect** to auto-find the fastest DNS, or browse the provider list
3. Click **Apply** to set the DNS
4. Use **Default DNS** to reset to automatic
5. Star your favorite providers for quick access
6. Use the search bar to find any DNS by name or IP address
7. Save custom DNS presets from the Custom DNS card
8. Set up **Network Profiles** via the menu to auto-switch DNS per network
9. Minimize to system tray — app keeps running in the background
10. Check for updates via the menu (three dots)

## Building from Source

```bash
# Install runtime and development dependencies
pip install -r requirements-dev.txt

# Run directly
python main.py

# Build executables (DNSChanger.exe + Updater.exe + DNSHelper.exe)
build.bat

# Build installer locally (requires NSIS)
makensis installer.nsi

# Recommended public release: push a version tag and let GitHub Actions build,
# checksum, and upload the exact Auto Update assets (see docs/RELEASING.md)
```

## Project Structure

```
dns-jantex/
├── main.py                    # Application entry point
├── updater.py                 # Standalone verified-update installer
├── helper.py                  # Narrow elevated DNS-operation helper
├── VERSION                    # Current version string
├── ui/                        # User interface
│   ├── main_window.py         # Main window + system tray + updater UI
│   ├── components.py          # UI components (DNSCard, NetworkInfoCard, etc.)
│   ├── styles.py              # Themes and styles
│   ├── animated_menu.py       # Animated preferences menu
│   ├── animations.py          # Reusable animation utilities
│   ├── custom_dns_dialog.py   # Custom DNS manager dialog
│   ├── network_profile_dialog.py  # Network profile manager dialog
│   └── toast.py               # Desktop toast notifications
├── core/                      # Core logic
│   ├── dns_manager.py         # DNS operations
│   ├── dns_providers.py       # Validated IPv4 provider list (45+)
│   ├── network_adapter.py     # Network detection + Wi-Fi SSID
│   ├── custom_dns.py          # Custom DNS persistent storage
│   ├── network_profiles.py    # Network profile data model + CRUD
│   ├── network_monitor.py     # Background network change detection
│   ├── powershell.py          # Escaped PowerShell command executor
│   ├── elevated_client.py     # UAC helper client
│   ├── validation.py          # Shared IPv4 validation
│   ├── paths.py               # Per-user LocalAppData paths
│   ├── storage.py             # Atomic JSON persistence
│   └── updater.py             # Update checker (GitHub Releases API)
├── translations/              # Language files
│   ├── en.json
│   └── fa.json
├── assets/                    # Icons and images
│   └── icons/                 # SVG icon set
├── build.bat                  # Build script (app + updater)
├── build.spec                 # PyInstaller config for main app
├── build_updater.spec         # PyInstaller config for updater
├── build_helper.spec          # PyInstaller config for elevated helper
└── installer.nsi              # NSIS installer script
```

## What's New in v3.0.4

### Safer privilege model
The main UI now runs as a normal user. A small, allow-listed helper requests UAC
only for Set, Reset, and Flush, validates all input again after elevation, and
never accepts arbitrary PowerShell commands.

### Verified automatic updates
The updater requires the exact Installer and checksum-manifest assets, enforces
the declared size, and checks SHA-256 before execution. If a Code Signing
Certificate is configured, a pinned Authenticode signer is required as a second
independent check. See [Releasing](docs/RELEASING.md) and [Code Signing](docs/CODE_SIGNING.md).

### Reliable state and persistence
Language and skipped-update state persist correctly, providers are stored by a
stable name instead of a sortable index, JSON writes are atomic, and user data
is migrated to `%LOCALAPPDATA%\DNS Jantex`.

### Real DNS benchmarks
Smart Connect now sends DNS queries instead of ICMP pings, honors its timeout,
and ranks providers using the median of three samples.

### Development quality
The provider list is checked for invalid and duplicate pairs, IPv4 validation is
shared across every input path, and CI runs compilation, linting, and tests on
Windows and Linux with Python 3.10 and 3.12.

## Support

If you find DNS Jantex useful, consider supporting the development:

[![Donate](https://img.shields.io/badge/Donate-Daramet-orange)](https://daramet.com/ZeLoExE)

## License

MIT License - see [LICENSE.txt](LICENSE.txt)

## Credits

Built with [PySide6](https://doc.qt.io/qtforpython-6/), [psutil](https://github.com/giampaolo/psutil), and [NSIS](https://nsis.sourceforge.io/).
