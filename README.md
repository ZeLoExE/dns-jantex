<p align="center">
  <img src="docs/icon.png" width="100">
</p>

<h1 align="center">DNS Jantex</h1>

<p align="center">
  A modern Windows DNS management app with 50+ providers, latency testing, Smart Connect, and Persian support.
</p>

---

## Features

- **50+ DNS providers** — Google, Cloudflare, Quad9, AdGuard, and many more
- **Smart Connect** — one-click benchmark that auto-selects the fastest provider
- **Tag filters** — filter providers by Gaming, Ad Blocking, Family Safe, Privacy, Security, or Anti-Sanction
- **Favorites system** — star your most-used DNS providers to pin them to the top of the list
- **Sticky search bar** — search stays accessible as you scroll through the provider list
- **Custom DNS presets** — save frequently used manual DNS inputs for quick access
- **Network Stream graph** — real-time bandwidth monitor showing upload/download speed
- **Ping Stat chart** — line chart tracking latency history over time
- **DNS analytics** — live uptime, success rate, and query count displayed in real time
- **Status indicator** — green/yellow/red dot shows DNS health at a glance
- **Auto-Flush DNS** — optionally flush DNS cache automatically after every Apply
- **Dark & light themes** — switch with one click, fully theme-aware UI
- **English & Persian** — full Farsi language support with RTL layout
- **One-click apply** — fast DNS switching with instant confirmation
- **Flush & reset** — clear DNS cache or restore automatic (DHCP) settings
- **Manage DNS modal** — add, edit, and delete custom DNS entries with a unified data store
- **Installer** — desktop and Start Menu shortcuts included

## Screenshots

<p align="center">
  <img src="docs/screenshot-dark.png" width="700">
  <br>
  <em>Dark mode</em>
</p>

## Download

Download the latest installer from [Releases](https://github.com/ZeLoExE/dns-jantex/releases).

## Requirements

- Windows 10/11
- Administrator privileges (required to change DNS settings)
- Python 3.10+ (for building from source)
- psutil (for network bandwidth monitoring)

## Installation

1. Download `DNSJantex-Setup.exe` from [Releases](https://github.com/ZeLoExE/dns-jantex/releases)
2. Run the installer as Administrator
3. Follow the setup wizard

## Usage

1. Run `DNSChanger.exe` as Administrator
2. Click **Smart Connect** to auto-find the fastest DNS, or browse the list
3. Click **Apply** to set the DNS
4. Use **Default DNS** to reset to automatic
5. Star your favorite providers for quick access
6. Use the search bar to find any DNS by name or IP address
7. Save custom DNS presets from the Custom DNS card

## Building from Source

```bash
# Install dependencies
pip install -r requirements.txt

# Run directly
python main.py

# Build executable
pyinstaller build.spec

# Build installer (requires NSIS)
makensis installer.nsi
```

## Project Structure

```
dns-jantex/
├── main.py                 # Application entry point
├── ui/                     # User interface
│   ├── main_window.py      # Main window
│   ├── components.py       # UI components (DNSCard, NetworkInfoCard, etc.)
│   ├── styles.py           # Themes and styles
│   └── custom_dns_dialog.py
├── core/                   # Core logic
│   ├── dns_manager.py      # DNS operations
│   ├── dns_providers.py    # Provider list (50+)
│   ├── network_adapter.py  # Network detection
│   └── custom_dns.py       # Custom DNS persistent storage
├── translations/           # Language files
│   ├── en.json
│   └── fa.json
├── assets/                 # Icons and images
│   └── icons/              # SVG icon set
├── build.spec              # PyInstaller config
└── installer.nsi           # NSIS installer script
```

## What's New in v2.0

- **Favorites system** — star providers to pin them to the top
- **Network Stream graph** — real-time bandwidth monitoring
- **Sticky search** — search bar stays visible while scrolling
- **Custom DNS presets** — save and reuse manual DNS inputs
- **Auto-Flush DNS** — optional automatic cache flush after Apply
- **Light mode fixes** — fully working light theme with proper contrast
- **Unified data store** — Custom DNS presets and Manage DNS share one backend
- **Two-row action bar** — cleaner layout with tags and buttons separated
- **Removed redundant controls** — Test Latency button removed (covered by Test Speed & Stability)
- **Improved typography** — larger fonts, better spacing, no text clipping

## License

MIT License - see [LICENSE.txt](LICENSE.txt)

## Credits

Built with [PySide6](https://doc.qt.io/qtforpython-6/), [psutil](https://github.com/giampaolo/psutil), and [NSIS](https://nsis.sourceforge.io/).
