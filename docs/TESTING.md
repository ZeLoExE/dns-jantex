# راهنمای تست DNS Jantex 3.0.4

> عملیات Apply، Reset و Flush واقعاً شبکه‌ی ویندوز را تغییر می‌دهند. تست عملی را
> ترجیحاً در Windows Sandbox یا یک ماشین مجازی انجام دهید و ابتدا تنظیمات فعلی
> DNS را یادداشت کنید.

## ۱. آماده‌سازی

در PowerShell معمولی، نه Administrator:

```powershell
cd dns-jantex
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
```

اگر اجرای Activate مسدود بود:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\.venv\Scripts\Activate.ps1
```

## ۲. تست‌های خودکار

```powershell
.\run_tests.bat
```

یا به‌صورت دستی:

```powershell
python -m compileall -q .
python -m pytest -v
python -m ruff check core ui main.py helper.py updater.py tests
```

باید ۲۱ تست یا بیشتر Pass شوند و هیچ خطای Compile یا Ruff وجود نداشته باشد.

## ۳. اجرای سورس

```powershell
python main.py
```

انتظار می‌رود:

- برنامه هنگام شروع UAC درخواست نکند.
- رابط کاربری عادی باز شود.
- تنظیمات در `%LOCALAPPDATA%\DNS Jantex` نوشته شوند، نه Program Files.
- انتخاب فارسی پس از بستن و اجرای دوباره حفظ شود.

## ۴. تست Helper و UAC

ابتدا وضعیت فعلی را ثبت کنید:

```powershell
Get-DnsClientServerAddress -AddressFamily IPv4 |
  Where-Object ServerAddresses |
  Format-Table InterfaceAlias, ServerAddresses -Auto
```

سپس در برنامه Cloudflare یا Google را انتخاب و Apply کنید.

انتظار می‌رود:

1. فقط در لحظه‌ی Apply پنجره‌ی UAC نمایش داده شود.
2. نام برنامه‌ی Elevateشده `python.exe` در حالت توسعه و `DNSHelper.exe` در Build باشد.
3. پس از تأیید، DNS تغییر کند و Helper بسته شود.
4. با Cancel کردن UAC، برنامه Crash نکند و پیام لغو دسترسی نشان دهد.
5. واردکردن `999.1.1.1` قبل از UAC رد شود.

بررسی نتیجه:

```powershell
Get-DnsClientServerAddress -AddressFamily IPv4 |
  Where-Object ServerAddresses |
  Format-Table InterfaceAlias, ServerAddresses -Auto
Resolve-DnsName example.com
```

در پایان روی **Default DNS** کلیک کنید تا تنظیمات DHCP برگردد.

## ۵. تست Auto Flush

### خاموش

1. گزینه‌ی Auto Flush DNS را خاموش کنید.
2. کش را با یک Query پر کنید:

```powershell
Resolve-DnsName example.com
Get-DnsClientCache | Where-Object Entry -Like '*example.com*'
```

3. Apply کنید. انتظار می‌رود برنامه Flush اضافه انجام ندهد.

### روشن

1. Auto Flush DNS را روشن کنید.
2. دوباره کش را پر و Apply کنید.
3. بعد از عملیات، رکورد قبلی نباید در `Get-DnsClientCache` باقی مانده باشد.

این تست تأیید می‌کند حالت خاموش یک بار و حالت روشن دو بار Flush نمی‌کند؛ Flush
فقط در حالت روشن و داخل همان Helper انجام می‌شود.

## ۶. تست Smart Connect

روی Smart Connect کلیک کنید. انتظار می‌رود:

- برای هر Provider سه Query واقعی DNS گرفته شود.
- Median سه نمونه نمایش داده شود.
- UI هنگام Benchmark هنگ نکند.
- Provider سریع‌تر انتخاب شود، ولی تا کلیک Apply تغییری در DNS سیستم ایجاد نشود.

برای مشاهده‌ی فنی می‌توان در Wireshark از فیلتر زیر استفاده کرد:

```text
udp.port == 53
```

باید ترافیک DNS دیده شود، نه تعداد زیادی Process از PowerShell و نه صرفاً ICMP.

## ۷. تست Settings و داده‌ها

- زبان را فارسی کنید، برنامه را ببندید و دوباره باز کنید.
- Providerها را Sort کنید، یک Provider انتخاب کنید و Restart کنید؛ همان نام باید
  انتخاب شود، نه Provider دیگری با همان Index قدیمی.
- یک Custom DNS و Network Profile بسازید و فایل‌های زیر را بررسی کنید:

```text
%LOCALAPPDATA%\DNS Jantex\settings.json
%LOCALAPPDATA%\DNS Jantex\custom_dns.json
%LOCALAPPDATA%\DNS Jantex\network_profiles.json
```

برای تست بازیابی خرابی JSON، روی VM یکی از فایل‌ها را خراب کنید. برنامه نباید
Crash کند و فایل باید با پسوند `.corrupt-<timestamp>` نگه‌داری شود.

## ۸. تست Network Profile

1. یک Profile برای SSID فعلی بسازید.
2. DNS را به مقدار دیگری تغییر دهید.
3. Wi-Fi را قطع و وصل کنید.
4. با Auto-Switch خاموش باید تأییدیه نمایش داده شود.
5. با Auto-Switch روشن باید Helper درخواست UAC بدهد و Profile اعمال شود.
6. اگر DNS از قبل برابر Profile است، نباید دوباره Apply یا اعلان تکراری انجام شود.

## ۹. تست Auto Update با SHA-256

Release آزمایشی باید هر دو فایل زیر را داشته باشد:

```text
DNSJantex-Setup.exe
DNSJantex-checksums.json
```

برای شبیه‌سازی نسخه‌ی جدید، از Workflow آزمایشی توضیح‌داده‌شده در
[RELEASING.md](RELEASING.md) استفاده کنید. انتظار می‌رود:

- دکمه `Install Verified Update` باشد.
- اندازه و SHA-256 پیش از اجرا بررسی شوند.
- تغییر یک Byte از Installer باعث Block شدن شود.
- تغییر اندازه یا Hash در Manifest باعث Block شدن شود.
- حذف یا تغییر نام هرکدام از دو Asset باعث شود Update معتبر شناخته نشود.
- Updater مستقل پیش از UAC دوباره SHA-256 را محاسبه کند.

نبود Certificate مانع Auto Update نیست؛ Certificate فقط یک لایه‌ی امنیتی دوم
به SHA-256 اضافه می‌کند.

## ۱۰. تست Updater امضاشده

این تست را فقط در VM و بعد از تهیه‌ی Certificate انجام دهید:

1. Thumbprint چهل‌کاراکتری Certificate را بدون فاصله در
   `SIGNING_CERTIFICATE.txt` قرار دهید.
2. Build بگیرید.
3. `DNSChanger.exe`، `Updater.exe`، `DNSHelper.exe` و Installer نهایی را با همان
   Certificate و RFC 3161 Timestamp امضا کنید.
4. وضعیت را بررسی کنید:

```powershell
Get-AuthenticodeSignature .\DNSJantex-Setup.exe |
  Format-List Status, StatusMessage, SignerCertificate
```

5. یک Installer سالم با همان Certificate باید پذیرفته شود.
6. تغییر حتی یک Byte از Installer باید باعث `HashMismatch` و Block شدن شود.
7. Installer امضاشده با Certificate دیگر نیز باید به‌علت Thumbprint متفاوت Block شود.

جزئیات بیشتر در [CODE_SIGNING.md](CODE_SIGNING.md) آمده است.

## ۱۱. تست Build و Installer

```powershell
.\build.bat
makensis installer.nsi
```

خروجی‌های مورد انتظار:

```text
dist\DNSChanger\DNSChanger.exe
dist\Updater.exe
dist\DNSHelper.exe
DNSJantex-Setup.exe
```

روی یک VM تمیز بررسی کنید:

- نصب و حذف برنامه
- Shortcutها
- اجرای UI بدون UAC
- UAC فقط هنگام عملیات DNS
- Upgrade از 3.0.3 و انتقال تنظیمات قدیمی به LocalAppData
- اجرای برنامه روی DPIهای 100٪، 125٪ و 150٪

## چک‌لیست قبولی نهایی

- [ ] همه‌ی تست‌های خودکار Pass هستند.
- [ ] شروع برنامه UAC ندارد.
- [ ] Apply/Reset/Flush فقط از Helper انجام می‌شوند.
- [ ] لغو UAC امن و بدون Crash است.
- [ ] Smart Connect Query واقعی DNS می‌فرستد.
- [ ] زبان و Provider پس از Restart حفظ می‌شوند.
- [ ] Auto Flush دقیقاً مطابق Toggle عمل می‌کند.
- [ ] JSON خراب باعث حذف بی‌صدا یا Crash نمی‌شود.
- [ ] Auto Update فقط با Manifest، اندازه و SHA-256 معتبر اجرا می‌شود.
- [ ] Installer دستکاری‌شده یا Manifest نامعتبر Block می‌شود.
- [ ] در Build امضاشده، Signer متفاوت نیز Block می‌شود.
- [ ] Default DNS در پایان تست شبکه را به DHCP برمی‌گرداند.
