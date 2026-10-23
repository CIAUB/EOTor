<div dir="rtl">

<h1 align="center">🚀 EOTor Engine</h1>

<p align="center">
<img src="https://readme-typing-svg.demolab.com?font=Fira+Code&size=20&pause=1000&color=8B0000&center=true&vCenter=true&width=500&lines=Sharingan-sharp+Routing;Multi-Location+SOCKS5;Silent+Precision;Developed+by+CIAUB" alt="Typing SVG" />
</p>

<p align="center">
<img src="https://img.shields.io/badge/Developer-CIAUB-8B0000.svg" />
<img src="https://img.shields.io/badge/Version-v4.0.0-8B0000.svg" />
<img src="https://img.shields.io/badge/Language-Python-8B0000.svg" />
<img src="https://img.shields.io/badge/Platform-Linux-8B0000.svg" />
<img src="https://img.shields.io/badge/License-MIT-8B0000.svg" />
</p>

**توسعه‌دهنده:** **CIAUB**  

> تمامی حقوق این پروژه متعلق به **CIAUB** است. هرگونه کپی‌برداری، تغییر یا انتشار مجدد باید با ذکر نام توسعه‌دهنده اصلی (CIAUB) انجام شود.

**مدیر حرفه‌ای نودهای SOCKS5 مبتنی بر Tor با پشتیبانی از صدها لوکیشن مختلف**

EOTor Engine یک ابزار مدیریت و استقرار نودهای SOCKS5 روی Linux است که امکان نصب، مدیریت، مانیتورینگ و کنترل صدها لوکیشن مختلف را از طریق یک رابط کاربری ترمینالی (TUI) فراهم می‌کند.

از نسخه **v4.0.0** پروژه‌ی **EZ-Panel** داخل EOTor ادغام شده است؛ یعنی ساخت اینباند و روتینگ لوکیشن‌ها در پنل‌های **3X-UI** و **PasarGuard** هم از همین ابزار انجام می‌شود (منوی `[8] Panel Integration`).

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

✅ اتصال به پنل 3X-UI و PasarGuard (ادغام EZ-Panel)

✅ رابط کاربری ترمینالی مدرن، رنگی و هم‌تراز

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
[8] Panel Integration
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

### 🔒 IP Leak & Block Check (v3.5.1 جدید)

اسکن همه‌ی نودهای فعال برای سه موضوع امنیتی:

* **Tor Verification** — بررسی اینکه IP خروجی واقعاً یک Tor exit هست (`check.torproject.org/api/ip`)
* **DNS Leak Check** — تشخیص نشت DNS از طریق Tor (`ipleak.net/json/`)
* **Blacklist Check** — بررسی بلاک بودن IP در Spamhaus ZEN DNSBL

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

# 🖥 Panel Integration (EZ-Panel)

با انتخاب `[8] Panel Integration` پنل نصب‌شده روی سرور شناسایی می‌شود (3X-UI یا PasarGuard؛ Marzban به‌زودی). اگر فقط یک پنل پیدا شود مستقیم وارد آن می‌شوید.

| گزینه                  | عملکرد                                                        |
| ---------------------- | ------------------------------------------------------------- |
| Batch create           | ساخت کانفیگ همه‌ی ۵۰ لوکیشن اصلی از روی یک اینباند موجود      |
| Custom create          | ساخت کانفیگ برای لوکیشن‌های انتخابی                           |
| Sync deployed modules  | افزودن نودهای EOTor که نصب شده‌اند ولی هنوز در پنل نیستند     |
| Delete                 | حذف همه یا بخشی از کانفیگ‌های EOTor از پنل                    |

برای هر لوکیشن یک اینباند روی پورت پنل، یک Outbound از نوع SOCKS و یک Routing Rule ساخته می‌شود:

```text
پورت اینباند پنل: 3031 - 3080   ➔   SOCKS محلی EOTor: 9080 - 9129
```

> Outbound ها با نام `EoTor-<COUNTRY>` ساخته می‌شوند. کانفیگ‌های قدیمی EZ-Panel (`T.Sin-<COUNTRY>`) هم شناسایی و هنگام حذف پاک می‌شوند.

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
eotor.py            ← موتور EOTor + ادغام EZ-Panel (یک فایل)
tests/test_eotor.py
README.md
LICENSE
```

---

<p align="center">
<img src="https://raw.githubusercontent.com/CIAUB/CIAUB/main/sharingan.jpg" width="500" alt="Sharingan" />
</p>

---

---

# 👨‍💻 توسعه‌دهنده (Developer)

| فیلد          | مقدار                                            |
| ------------- | ------------------------------------------------ |
| **نام**       | **CIAUB**                                        |
| **نقش**       | طراح و توسعه‌دهنده اصلی (Original Author)       |
| **GitHub**    | [github.com/CIAUB](https://github.com/CIAUB)     |
| **پروژه**     | [github.com/CIAUB/EOTor](https://github.com/CIAUB/EOTor) |

> تمامی حقوق این پروژه متعلق به **CIAUB** است.

---

# 📞 ارتباط با ما

### 📢 کانال تلگرام

**@CIAUB_CH**

https://t.me/CIAUB_CH

---

### 👨‍💻 پشتیبانی

**@CIAUB**

https://t.me/CIAUB

---

# ❤️ حمایت از پروژه

اگر این پروژه برای شما مفید بوده است، با عضویت در کانال تلگرام از آخرین بروزرسانی‌ها، آموزش‌ها و قابلیت‌های جدید مطلع شوید.

---

# 📄 License

MIT License

</div>
