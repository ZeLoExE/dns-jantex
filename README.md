# DNS Jantex

A modern Windows DNS management application built with PySide6.

## Features

- Switch between 50+ DNS providers worldwide with one click
- Built-in latency test to find the fastest DNS for your connection
- Sort providers by name or ping speed
- Iran DNS filter for quick access to local providers
- Custom DNS support — add your own DNS servers
- Dark and light themes
- English and Persian (Farsi) language support
- Flush DNS cache and reset to DHCP
- System tray support
- Desktop and Start Menu shortcuts via installer

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

## Installation

1. Download `DNSJantex-Setup.exe` from Releases
2. Run the installer as Administrator
3. Follow the setup wizard

## Usage

1. Run `DNSChanger.exe` as Administrator
2. Select a DNS provider from the list
3. Click **Apply** to set the DNS
4. Use **Test Latency** to compare speeds
5. Use **Default DNS** to reset to automatic

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
│   ├── components.py       # UI components
│   ├── styles.py           # Themes and styles
│   └── custom_dns_dialog.py
├── core/                   # Core logic
│   ├── dns_manager.py      # DNS operations
│   ├── dns_providers.py    # Provider list
│   ├── network_adapter.py  # Network detection
│   └── custom_dns.py       # Custom DNS storage
├── translations/           # Language files
│   ├── en.json
│   └── fa.json
├── assets/                 # Icons and images
├── config/                 # User settings
├── build.spec              # PyInstaller config
└── installer.nsi           # NSIS installer script
```

## License

MIT License - see [LICENSE.txt](LICENSE.txt)

## Credits

Built with [PySide6](https://doc.qt.io/qtforpython-6/) and [NSIS](https://nsis.sourceforge.io/).
