<div dir="rtl">

# 🚀 EOTor Engine

![Version](https://img.shields.io/badge/Version-v3.4-blue.svg)
![Python](https://img.shields.io/badge/Language-Python-green.svg)
![Platform](https://img.shields.io/badge/Platform-Linux-orange.svg)
![License](https://img.shields.io/badge/License-MIT-red.svg)

**مدیر چندمکانه پراکسی SOCKS5 — نصب خودکار، مدیریت آسان و استقرار سریع**

EOTor Engine یک ابزار حرفه‌ای مدیریت نودهای SOCKS5 مبتنی بر Tor است که امکان نصب، مدیریت، مانیتورینگ و کنترل صدها لوکیشن مختلف را از طریق یک رابط کاربری ترمینالی (TUI) فراهم می‌کند.

---

# ✨ ویژگی‌ها

✅ نصب خودکار تنها با یک دستور

✅ مدیریت بیش از 200 لوکیشن مختلف

✅ استقرار موازی نودها

✅ مانیتورینگ زنده وضعیت نودها

✅ نمایش IP خروجی هر لوکیشن

✅ سیستم Health Check داخلی

✅ سیستم Auto Restart

✅ سیستم CPU Guardian

✅ نصب و حذف گروهی نودها

✅ مدیریت کامل از طریق منوی ترمینال

✅ بدون نیاز به تنظیمات پیچیده

---

# 🛠 نصب

برای نصب EOTor Engine کافی است با دسترسی Root دستور زیر را اجرا کنید:

```bash
sudo bash -c "$(curl -sL "https://raw.githubusercontent.com/EOAMIR/EOTor/main/install.sh")"
```

پس از پایان نصب، برای اجرای مجدد برنامه از دستور زیر استفاده کنید:

```bash
sudo eotor
```

---

# 📋 پیش‌نیازها

| مورد       | توضیحات       |
| ---------- | ------------- |
| سیستم‌عامل | Ubuntu 20.04+ |
| سیستم‌عامل | Debian 10+    |
| دسترسی     | Root          |
| اینترنت    | الزامی        |

تمام وابستگی‌های موردنیاز به‌صورت خودکار توسط نصب‌کننده دریافت و نصب می‌شوند.

---

# 🗂 منوی اصلی

```text
[1] Setup & Engine
[2] Install Location Modules
[3] Extended Modules
[4] Control Modules
[5] Monitoring & Diagnostics
[6] IP & Routing
[7] Automation & Guardian
[0] Exit
```

---

# ⚙️ Setup & Engine

| گزینه            | توضیح                  |
| ---------------- | ---------------------- |
| Install Engine   | نصب موتور و وابستگی‌ها |
| Update System    | بروزرسانی موتور        |
| Uninstall System | حذف کامل موتور و نودها |

---

# 🌍 Primary Location Modules

بخش اصلی برنامه شامل 50 لوکیشن پرکاربرد است.

پورت‌های:

```text
9080 → 9129
```

نمونه لوکیشن‌ها:

* Germany
* Turkey
* United States
* France
* Canada
* Singapore
* Japan
* United Kingdom
* Finland
* Ireland
* Austria
* Belgium

و ده‌ها کشور دیگر.

---

# 🌎 Extended Location Modules

بیش از 163 لوکیشن اضافه در این بخش قرار دارند.

نمونه کشورها:

* Brazil
* Egypt
* Afghanistan
* Nigeria
* Chile
* Peru
* Morocco
* Pakistan
* South Africa
* Mexico

و بسیاری از کشورهای دیگر.

---

# 🎮 Control Modules

امکانات مدیریتی:

* Start Modules
* Stop Modules
* Restart Modules
* Remove Modules
* Start All
* Stop All
* Restart All
* Remove All

---

# 📊 Monitoring & Diagnostics

سیستم مانیتورینگ داخلی شامل:

### Live Status Table

نمایش وضعیت تمام نودها

### Health Check

تست اتصال تمام نودهای فعال

### Relay Density

بررسی تعداد رله‌های موجود برای هر کشور

### Exit IP Viewer

نمایش IP خروجی هر نود

### Node Diagnostics

بررسی وضعیت سرویس و لاگ‌ها

---

# 🔄 IP & Routing

### Deploy Module

استقرار نود با نمایش درصد پیشرفت

### Live IP Panel

نمایش زنده IP خروجی نودها

### Rotate IP

تغییر IP خروجی نودهای انتخابی

---

# 🤖 Automation & Guardian

### Auto Restart

امکان ری‌استارت خودکار ساعتی تمام نودها.

### CPU Guardian

نظارت دائمی روی مصرف CPU:

* بررسی هر 5 دقیقه
* توقف خودکار نودهای پرمصرف
* راه‌اندازی مجدد پس از 1 ساعت
* ثبت کامل رویدادها

---

# 📡 محدوده پورت‌ها

| محدوده      | تعداد              |
| ----------- | ------------------ |
| 9080 - 9129 | 50 لوکیشن اصلی     |
| 9130+       | 163+ لوکیشن گسترده |

تمام نودها روی:

```text
127.0.0.1:<PORT>
```

در دسترس خواهند بود.

---

# 📁 ساختار پروژه

```text
install.sh
README.md
.gitignore
```

---

# 📞 ارتباط با ما

### 📢 کانال تلگرام

https://t.me/IMEOAMIR

### 👨‍💻 پشتیبانی

https://t.me/EOAMIR

---

# ❤️ حمایت از پروژه

اگر این پروژه برای شما مفید بوده است، با عضویت در کانال تلگرام از آخرین بروزرسانی‌ها، آموزش‌ها و قابلیت‌های جدید مطلع شوید.

---

# 📄 License

MIT License

</div>
