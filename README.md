<p align="center">
  <img src="docs/logo.png" width="100">
</p>

<h1 align="center">DNS Jantex</h1>

<p align="center">
  <img src="https://img.shields.io/badge/version-3.0.3-6366f1?style=for-the-badge" alt="Version">
  <img src="https://img.shields.io/badge/python-3.10+-3776ab?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/platform-Windows_10%2F11-0078d4?style=for-the-badge&logo=windows&logoColor=white" alt="Windows">
  <img src="https://img.shields.io/badge/license-MIT-22c55e?style=for-the-badge" alt="License">
  <a href="https://dns-jantex.pages.dev/"><img src="https://img.shields.io/badge/Website-dns--jantex.pages.dev-blue?style=for-the-badge&logo=googlechrome&logoColor=white" alt="Website"></a>
</p>

<p align="center">
  A modern Windows DNS management app with 70+ providers, network profiles, Smart Connect, toast notifications, system tray, auto-updater, and Persian support.
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

## Features

### DNS Management
- **70+ DNS providers** — Google, Cloudflare, Quad9, AdGuard, OpenDNS, Norton, Level3, and many more
- **Smart Connect** — one-click benchmark that auto-selects the fastest provider
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
- **DNS analytics** — live uptime, success rate, and query count displayed in real time
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
- **Auto-updater** — checks GitHub Releases for new versions, downloads and installs silently
- **Dark & light themes** — switch with one click, fully theme-aware UI
- **English & Persian** — full Farsi language support with RTL layout
- **Frameless window** — modern custom title bar with native Windows 11 shadow and rounded corners
- **Installer** — desktop and Start Menu shortcuts included

## Requirements

- Windows 10/11
- Administrator privileges (required to change DNS settings)

## Installation

1. Download `DNSJantex-Setup.exe` from [Releases](https://github.com/ZeLoExE/dns-jantex/releases)
2. Run the installer as Administrator
3. Follow the setup wizard
4. Launch DNS Jantex from Desktop or Start Menu

## Usage

1. Run **DNS Jantex** as Administrator
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
# Install dependencies
pip install -r requirements.txt

# Run directly
python main.py

# Build executables (DNSChanger.exe + Updater.exe)
build.bat

# Build installer (requires NSIS)
makensis installer.nsi
```

## Project Structure

```
dns-jantex/
├── main.py                    # Application entry point
├── updater.py                 # Standalone updater script
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
│   ├── dns_providers.py       # Provider list (70+)
│   ├── network_adapter.py     # Network detection + Wi-Fi SSID
│   ├── custom_dns.py          # Custom DNS persistent storage
│   ├── network_profiles.py    # Network profile data model + CRUD
│   ├── network_monitor.py     # Background network change detection
│   ├── powershell.py          # PowerShell command executor
│   └── updater.py             # Update checker (GitHub Releases API)
├── translations/              # Language files
│   ├── en.json
│   └── fa.json
├── assets/                    # Icons and images
│   └── icons/                 # SVG icon set
├── build.bat                  # Build script (app + updater)
├── build.spec                 # PyInstaller config for main app
├── build_updater.spec         # PyInstaller config for updater
└── installer.nsi              # NSIS installer script
```

## What's New in v3.0.0

### Network Profiles
Create DNS profiles linked to specific networks. When you connect to a recognized Wi-Fi network or Ethernet adapter, DNS Jantex can automatically apply the correct DNS settings or prompt you for confirmation.

### Toast Notifications
Desktop-level notifications that appear at the screen's bottom-right corner. They slide in smoothly, auto-dismiss after 3 seconds, and don't block interaction with the main window.

### Improved UI
All frameless dialogs now fade in smoothly. Interactive buttons have improved hover effects with icon color transitions. The preferences popup menu has a clean transparent background with proper rounded corners.

### Better DNS Management
Network profile detection always runs in the background. The Auto Switch setting only controls whether profiles are applied silently or shown with a confirmation dialog, giving you full control.

## Support

If you find DNS Jantex useful, consider supporting the development:

[![Donate](https://img.shields.io/badge/Donate-Daramet-orange)](https://daramet.com/ZeLoExE)

## License

MIT License - see [LICENSE.txt](LICENSE.txt)

## Credits

Built with [PySide6](https://doc.qt.io/qtforpython-6/), [psutil](https://github.com/giampaolo/psutil), and [NSIS](https://nsis.sourceforge.io/).
