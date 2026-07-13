# انتشار نسخه در GitHub

فرایند Release برای Windows در `.github/workflows/release.yml` خودکار شده است.
این Workflow روی Windows برنامه، Updater، Helper و NSIS Installer را می‌سازد،
تست‌ها را اجرا می‌کند، `DNSJantex-checksums.json` می‌سازد و هر دو فایل را به
GitHub Release اضافه می‌کند.

## انتشار 3.0.4

پس از جایگزین‌کردن فایل‌های اصلاح‌شده در Clone اصلی مخزن:

```powershell
git checkout main
git add -A
git commit -m "Release v3.0.4: stability, secure helper, verified updates"
git push origin main
git tag -a v3.0.4 -m "DNS Jantex 3.0.4"
git push origin v3.0.4
```

Push شدن Tag، Workflow را اجرا و Release عمومی را ایجاد می‌کند. وضعیت آن در
تب **Actions** مخزن قابل مشاهده است.

## Build آزمایشی بدون Release

از تب Actions، Workflow با نام **Build and publish Windows release** را انتخاب
کنید، `Run workflow` را بزنید و گزینه‌ی `publish` را خاموش نگه دارید. خروجی در
بخش Artifacts همان Run قابل دانلود است.

## قوانین سازگاری Auto Update

نام این دو Asset نباید تغییر کند:

```text
DNSJantex-Setup.exe
DNSJantex-checksums.json
```

فایل Manifest باید فقط شامل Installer، اندازه‌ی دقیق و SHA-256 آن باشد. Workflow
این فایل را خودکار تولید می‌کند.

## امضای دیجیتال آینده

SHA-256 از خرابی، جایگزینی فایل پس از دانلود و عدم تطابق با Release Manifest
جلوگیری می‌کند؛ اما Manifest و Installer هر دو تحت اعتماد حساب GitHub هستند.
برای امنیت کامل زنجیره‌ی انتشار، بعداً Code Signing Certificate اضافه کنید.
در آن حالت Thumbprint را در `SIGNING_CERTIFICATE.txt` قرار داده و مراحل Sign را
پیش از ساخت Manifest به Workflow اضافه کنید.

هیچ‌گاه PFX، Password یا Personal Access Token را Commit نکنید. برای امضا فقط
از GitHub Actions Secrets استفاده کنید. برای انتشار عادی، Workflow از
`GITHUB_TOKEN` داخلی GitHub استفاده می‌کند و نیازی به ارسال Token در چت نیست.
