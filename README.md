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
[![License: GPL-3.0](https://img.shields.io/badge/License-GPL--3.0-blue.svg?style=for-the-badge&color=10b981)](LICENSE)

<br/>

<img src="assets/dns-jantex-v4-preview.png" alt="DNS Jantex v4.0.0 UI" width="780" style="border-radius: 12px; box-shadow: 0 8px 30px rgba(0,0,0,0.5);" />

</div>

---

## 🌟 English Overview

**DNS Jantex v4.0.0** is a major architectural revolution. Replacing the legacy Python/PySide6 implementation, this new version has been rebuilt from the ground up using **Rust** and **Tauri v2**, paired with a sleek **React + TypeScript + Tailwind CSS** frontend.

### ✨ Key Features
- ⚡ **Ultra-Lightweight & Fast:** Installer reduced from **~80 MB** to **under 6 MB**; launches instantaneously with near-zero RAM footprint (~40 MB).
- 🎯 **Real DNS UDP Port 53 Ping:** Concurrently tests true DNS lookup round-trip latency over raw UDP sockets (not deceptive ICMP pings) with strict 1.5s timeouts.
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

## 🔒 Security, Trust & Why Administrator Privileges? | چرا متن‌باز و نیازمند دسترسی ادمین؟

### 🇬🇧 English
- **Why Administrator Privileges?** Modifying Windows network adapter DNS addresses natively requires Windows Administrator privileges. DNS Jantex only requests elevation to configure your network adapter DNS table and flush the system resolver cache.
- **100% Open-Source & Transparent:** Because DNS tools manage critical internet routing parameters, DNS Jantex is completely open-source under GNU GPLv3. Every line of backend Rust and frontend React code is published right here for anyone to inspect and audit.
- **Windows SmartScreen Note:** Fresh releases of independent open-source tools without multi-thousand-dollar corporate EV code-signing certificates may trigger a Windows SmartScreen warning (*"Windows protected your PC"*). This is completely normal for new community software. You can safely click **"More info"** &rarr; **"Run anyway"**. You can verify the integrity of any downloaded binary using the SHA-256 hashes listed below.

### 🇮🇷 فارسی
- **دلیل نیاز به دسترسی Administrator:** در سیستم‌عامل ویندوز، تغییر آی‌پی سرورهای DNS هر کارت شبکه ذاتاً نیازمند دسترسی ادمین است. این برنامه تنها برای ثبت سرورها و پاکسازی کش DNS از این دسترسی استفاده می‌کند.
- **شفافیت کامل و متن‌باز:** با توجه به اهمیت امنیت ترافیک اینترنت، تمام سورس‌کد پروژه تحت لایسنس بین‌المللی GPLv3 به صورت ۱۰۰٪ عمومی و متن‌باز در دسترس است تا هر کاربری بتواند کارکرد امن آن را تأیید کند.
- **پیام Windows SmartScreen:** به دلیل هزینه چند هزار دلاری گواهی‌های تجاری EV در ویندوز، نرم‌افزارهای مستقل متن‌باز در اولین اجراها ممکن است با اخطار SmartScreen ویندوز مواجه شوند. این موضوع طبیعی بوده و می‌توانید با زدن **More info** و سپس **Run anyway** برنامه را اجرا کنید. همچنین با تطبیق چک‌سام SHA-256 زیر می‌توانید از اصالت فایل مطمئن شوید.

---

## 📦 Downloads & SHA-256 Checksums | دانلود و اعتبارسنجی

Official releases are hosted exclusively on the [GitHub Releases](https://github.com/ZeLoExE/dns-jantex/releases/latest) page:

| Package | Description | Size | SHA-256 Checksum |
| :--- | :--- | :--- | :--- |
| **`DNS-Jantex-v4.0.0-Setup.exe`** | Official Windows NSIS Installer | ~5.81 MB | `1c49ecae3a4e6c6030df365b9f6fd83b6caf27b6f257d3c33695abffee1b03bf` |
| **`DNS-Jantex-v4.0.0-Portable.exe`** | Standalone Portable (No install needed) | ~12.1 MB | `6d6ebb74d35519b6c5fa3717a08d9984a9e77e535db3bf113f84c4ee6b707325` |
| **`DNSJantex-Setup.exe`** | Legacy auto-updater compatible package | ~5.81 MB | `1c49ecae3a4e6c6030df365b9f6fd83b6caf27b6f257d3c33695abffee1b03bf` |

### Verify Checksum in PowerShell:
```powershell
Get-FileHash -Path "DNS-Jantex-v4.0.0-Setup.exe" -Algorithm SHA256
```

---

## 🛠️ Development & Building from Source

### Prerequisites
- [Node.js](https://nodejs.org/) (v18+ or v20+ LTS)
- [Rust](https://rustup.rs/) (stable toolchain `stable-x86_64-pc-windows-msvc`)
- Visual Studio C++ Build Tools (MSVC)
- WebView2 Runtime (Preinstalled on Windows 10/11)

### Setup & Run
```bash
# Clone the repository
git clone https://github.com/ZeLoExE/dns-jantex.git
cd dns-jantex

# Install frontend dependencies
npm install

# Run in development mode
npm run tauri dev

# Build production NSIS installer & binary
npm run tauri build
```

---

## 📄 License & Attribution

This project is licensed under the **GNU General Public License v3.0 (GPL-3.0)**.  
Copyright (C) 2026 **ZeLoExE**.

Under the terms of the GNU GPLv3:
- You are free to run, copy, distribute, study, and modify this software.
- If you modify or redistribute this software (or any derived work), your modifications **MUST** remain free and open-source under the same GPL-3.0 license.
- Proper credit and attribution to the original author (**ZeLoExE**) must always be preserved.

See the full [LICENSE](LICENSE) file for complete terms and conditions.
