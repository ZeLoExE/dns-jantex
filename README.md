<div align="center">

<img src="assets/icon.png" width="100" height="100" alt="DNS Jantex Logo" />

# DNS Jantex v4.0.0

**Modern, Lightweight Windows DNS & Network Profile Manager**  
*Re-engineered from scratch with Rust (Tauri v2) & React*

[![Release](https://img.shields.io/github/v/release/ZeLoExE/dns-jantex?style=for-the-badge&color=6366f1)](https://github.com/ZeLoExE/dns-jantex/releases/latest)
[![Tauri v2](https://img.shields.io/badge/Tauri-v2.0-24c8db?style=for-the-badge&logo=tauri&logoColor=white)](https://tauri.app)
[![Rust](https://img.shields.io/badge/Rust-2021_Edition-dea584?style=for-the-badge&logo=rust&logoColor=white)](https://www.rust-lang.org)
[![React](https://img.shields.io/badge/React-18+-61dafb?style=for-the-badge&logo=react&logoColor=black)](https://react.dev)
[![Platform](https://img.shields.io/badge/Platform-Windows_10%20%2F%2011-0078d4?style=for-the-badge&logo=windows&logoColor=white)](https://www.microsoft.com/windows)
[![License](https://img.shields.io/github/license/ZeLoExE/dns-jantex?style=for-the-badge&color=10b981)](LICENSE.txt)

<br/>

<img src="assets/dns-jantex-v4-preview.png" alt="DNS Jantex v4.0.0 UI" width="780" style="border-radius: 12px; box-shadow: 0 8px 30px rgba(0,0,0,0.5);" />

</div>

---

## 🌟 English Overview

**DNS Jantex v4.0.0** is a major architectural revolution. Replacing the legacy Python/PySide6 implementation, this new version has been rebuilt from the ground up using **Rust** and **Tauri v2**, paired with a sleek **React + TypeScript + Tailwind CSS** frontend.

### ✨ Key Features
- ⚡ **Ultra-Lightweight & Fast:** Installer reduced from **~80 MB** to **under 6 MB**; launches instantaneously with near-zero RAM footprint (~40 MB).
- 🎯 **Real DNS UDP Port 53 Ping:** Concurrently tests true DNS lookup round-trip latency over raw UDP sockets (not deceptive ICMP pings) with strict timeouts.
- 🔄 **Smart Network Profiles:** Automatically detects Wi-Fi SSID or Ethernet adapter switches and seamlessly applies your saved DNS configurations.
- 🧹 **Zero-Window Silent Auto-Flush:** Flushes the Windows DNS resolver cache silently using background flags without flashing any CMD or PowerShell windows.
- 🛡️ **Captive Portal Guard:** Automatically alerts you if hotel, airport, or cafe captive portal interception is detected on your network connection.
- 🪟 **Compact Frameless Windows 11 UI:** Fixed `840x680` high-density viewport with Mica dark aesthetic, single-row category filters, dual IP copy pills, and custom drag titlebar.
- 📥 **Background Tray Integration:** Closes to the Windows system tray with quick one-click actions ("Reset to DHCP", "Open", "Quit").

---

## 🇮🇷 معرفی فارسی (Persian Overview)

نسخه **DNS Jantex v4.0.0** یک تحول ساختاری بزرگ است. در این نسخه کدنویسی پایتون به‌طور کامل کنار گذاشته شده و برنامه از ابتدا با **راست (Rust)** و فریم‌ورک فوق‌سریع **Tauri v2** به همراه رابط کاربری مدرن **React + TypeScript + Tailwind CSS** بازنویسی شده است.

### ✨ ویژگی‌های کلیدی
- ⚡ **حجم فوق‌العاده کم و سرعت بی‌نظیر:** کاهش حجم فایل نصبی از **۸۰ مگابایت** به **کمتر از ۶ مگابایت** با مصرف رم بسیار بهینه (~۴۰ مگابایت).
- 🎯 **تست پینگ واقعی DNS از پورت ۵۳ (UDP):** اندازه‌گیری تأخیر واقعی با ارسال کوئری به پورت ۵۳ سرورها (به‌جای پینگ گمراه‌کننده ICMP) به صورت همزمان.
- 🔄 **پروفایل‌های هوشمند شبکه:** شناسایی خودکار نام شبکه Wi-Fi (SSID) یا آداپتور اترنت و تنظیم خودکار DNS متناسب با آن شبکه.
- 🧹 **فلاش خودکار بدون پرش پنجره:** پاکسازی کش DNS ویندوز بدون باز شدن هیچ‌گونه پنجره سیاه CMD یا پاورشل.
- 🛡️ **تشخیص صفحات لاگین عمومی (Captive Portal Guard):** هشدار هوشمند در صورت قرار گرفتن در شبکه هتل یا کافه برای جلوگیری از قطعی اتصال.
- 🪟 **طراحی مدرن و کامپکت ویندوز ۱۱:** رابط کاربری فریم‌لس شیشه‌ای در ابعاد بهینه، بدون اسکرول سراسری و با دسترسی فوق سریع به سرورهای گیمینگ، ضدتحریم و امنیت.
- 📥 **اجرا در پس‌زمینه (System Tray):** پشتیبانی از منوی اختصاصی آیکون کنار ساعت ویندوز با امکان ریست سریع به DHCP.

---

## 🚀 Installation & Download | راهنمای دانلود و نصب

### Windows (10 / 11)
Download the latest assets directly from the [GitHub Releases](https://github.com/ZeLoExE/dns-jantex/releases/latest) page:

| Package | Description | Size |
| :--- | :--- | :--- |
| **`DNS-Jantex-v4.0.0-Setup.exe`** | Official Windows NSIS Installer (Recommended) | ~5.8 MB |
| **`DNS-Jantex-v4.0.0-Portable.exe`** | Standalone Portable Executable (No installation required) | ~12 MB |
| **`DNSJantex-Setup.exe`** | Legacy auto-updater compatible installer package | ~5.8 MB |

> [!NOTE]  
> If you are updating from **v3.0.4**, opening your existing client and clicking **Update** will automatically download and install v4.0.0 seamlessly.

---

## 🛠️ Development & Building from Source

### Prerequisites
- [Node.js](https://nodejs.org/) (v18+ or v20+ LTS)
- [Rust](https://rustup.rs/) (stable toolchain)
- Visual Studio C++ Build Tools (MSVC)
- WebView2 Runtime (Included by default on Windows 10/11)

### Setup & Run
```bash
# Clone the repository
git clone https://github.com/ZeLoExE/dns-jantex.git
cd dns-jantex

# Install frontend dependencies
npm install

# Run development mode
npm run tauri dev

# Build production installer
npm run tauri build
```

---

## 📄 License
This project is licensed under the MIT License - see the [LICENSE.txt](LICENSE.txt) file for details.
