<div dir="rtl">

# 🚀 EOTor Engine

![Version](https://img.shields.io/badge/Version-v3.4-blue.svg)
![Python](https://img.shields.io/badge/Language-Python-green.svg)
![Linux](https://img.shields.io/badge/Platform-Linux-orange.svg)
![License](https://img.shields.io/badge/License-MIT-red.svg)

**مدیر حرفه‌ای نودهای SOCKS5 مبتنی بر Tor با پشتیبانی از صدها لوکیشن مختلف**

EOTor Engine یک ابزار مدیریت و استقرار نودهای SOCKS5 روی Linux است که امکان نصب، مدیریت، مانیتورینگ و کنترل صدها لوکیشن مختلف را از طریق یک رابط کاربری ترمینالی (TUI) فراهم می‌کند.

---

# ✨ امکانات

✅ نصب خودکار تنها با یک دستور

✅ مدیریت بیش از 200 لوکیشن مختلف

✅ استقرار موازی نودها

✅ مانیتورینگ زنده وضعیت نودها

✅ نمایش IP خروجی هر لوکیشن

✅ Health Check داخلی

✅ Auto Restart

✅ CPU Guardian

✅ مدیریت گروهی نودها

✅ نمایش وضعیت کامل سرویس‌ها

✅ رابط کاربری ساده و رنگی

---

# 🛠 نصب

برای نصب EOTor Engine کافی است با دسترسی Root دستور زیر را اجرا کنید:

```bash
sudo bash -c "$(curl -sL "https://raw.githubusercontent.com/CIAUB/EOTor/main/install.sh")"
```

اگر دستور بالا برای شما اجرا نشد، از لینک جایگزین زیر استفاده کنید:

```bash
sudo bash -c "$(curl -sL "https://raw.githack.com/CIAUB/EOTor/main/install.sh")"
```

> لینک دوم از CDN گیت‌هاب استفاده نمی‌کند و در برخی شبکه‌ها که دسترسی به `raw.githubusercontent.com` محدود است می‌تواند بدون مشکل اجرا شود.

پس از پایان نصب:

```bash
sudo eotor
```

---

# 📋 پیش‌نیازها

| مورد       | توضیحات       |
| ---------- | ------------- |
| سیستم عامل | Ubuntu 20.04+ |
| سیستم عامل | Debian 10+    |
| دسترسی     | Root          |
| اینترنت    | الزامی        |

تمام وابستگی‌ها به‌صورت خودکار نصب خواهند شد.

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

| گزینه            | عملکرد                 |
| ---------------- | ---------------------- |
| Install Engine   | نصب موتور و وابستگی‌ها |
| Update System    | بروزرسانی موتور        |
| Uninstall System | حذف کامل موتور و نودها |

---

# 🌍 Primary Location Modules

50 لوکیشن اصلی روی پورت‌های:

```text
9080 - 9129
```

نمونه کشورها:

* Germany
* Turkey
* United States
* France
* Canada
* Singapore
* Japan
* Austria
* Belgium
* Romania
* Finland
* Ireland
* United Kingdom

و ده‌ها کشور دیگر.

---

# 🌎 Extended Location Modules

بیش از 163 لوکیشن اضافه.

نمونه کشورها:

* Brazil
* Egypt
* Afghanistan
* Pakistan
* Nigeria
* Morocco
* Chile
* Peru
* Mexico
* South Africa

و بسیاری از کشورهای دیگر.

---

# 🎮 Control Modules

امکانات مدیریتی:

* Start Modules
* Stop Modules
* Restart Modules
* Remove Modules
* Start ALL Modules
* Stop ALL Modules
* Restart ALL Modules
* Remove ALL Modules

---

# 📊 Monitoring & Diagnostics

### Live Status Table

نمایش وضعیت تمامی نودها:

* Running
* Stopped
* Installed
* Not Installed

---

### Health Check

تست اتصال زنده روی تمام نودهای فعال.

---

### Relay Density

نمایش تعداد Exit Relay های هر کشور.

رنگ‌بندی:

🟢 بیش از 10 رله

🟡 بین 3 تا 9 رله

🔴 کمتر از 3 رله

---

### Exit IP Viewer

نمایش IP خروجی واقعی هر نود.

---

### Node Diagnostics

بررسی لاگ‌ها و وضعیت سرویس برای عیب‌یابی.

---

# 🔄 IP & Routing

### Deploy Module

استقرار نود همراه با نمایش درصد پیشرفت.

### Live IP Panel

نمایش زنده IP خروجی تمامی نودهای فعال.

### Rotate IP

تغییر IP خروجی نودهای انتخابی.

---

# 🤖 Automation & Guardian

## Auto Restart

ایجاد سرویس systemd جهت ری‌استارت خودکار ساعتی تمامی نودها.

---

## CPU Guardian

سرویس محافظ مصرف منابع:

* بررسی CPU هر 5 دقیقه
* توقف خودکار نودهای پرمصرف
* راه‌اندازی مجدد خودکار پس از 1 ساعت
* ثبت کامل رویدادها

---

# 📡 محدوده پورت‌ها

| محدوده      | تعداد              |
| ----------- | ------------------ |
| 9080 - 9129 | 50 لوکیشن اصلی     |
| 9130+       | 163+ لوکیشن گسترده |

تمام نودها روی آدرس زیر در دسترس هستند:

```text
127.0.0.1:<PORT>
```

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

**@IMEOAMIR**

https://t.me/IMEOAMIR

---

### 👨‍💻 پشتیبانی

**@EOAMIR**

https://t.me/EOAMIR

---

# ❤️ حمایت از پروژه

اگر این پروژه برای شما مفید بوده است، با عضویت در کانال تلگرام از آخرین بروزرسانی‌ها، آموزش‌ها و قابلیت‌های جدید مطلع شوید.

---

# 📄 License

MIT License

</div>
