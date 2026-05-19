# P2 - تفکیک فیچرها و ماژول‌های سیستم
**تاریخ:** ۱۴۰۵/۰۲/۲۵ | ۲۰۲۶/۰۵/۱۵  
**وضعیت:** ✅ تمام

---

## خلاصه
Rubifo یک ربات خودکار فوروارد برای روبیکا است که:
- کاربران می‌توانند مسیرهای مختلف (از کانال مبدأ به مقصد) تعریف کنند
- برای هر مسیر، پلان‌های زمانبندی مختلف ایجاد کنند
- پست‌ها به صورت خودکار و بدون تکرار فوروارد شوند

---

## ۱. ماژول User Management

### وظایف
- ثبت‌نام کاربران جدید (`/start`)
- مدیریت تریال ۴۸ ساعتی
- پیام یادآوری قبل از اتمام تریال (۲۴ ساعت قبل)
- مدیریت وضعیت کاربر (trial / active / inactive)

### خروجی Database
- `users` table: id, user_id, username, trial_start, trial_end, created_at

### وابستگی
- Subscription Management (برای فعال‌سازی اشتراک)
- Logging (برای ثبت رویدادها)

### V1 / Post-V1
- V1: ثبت‌نام، تریال، پیام یادآوری
- Post-V1: Social login، Two-factor auth

---

## ۲. ماژول Subscription & Payment

### وظایف
- سه سطح اشتراک: Basic (۱ کانال مقصد)، Pro (۳ کانال مقصد)، Enterprise (۱۰ کانال مقصد)
- اتصال به درگاه زرین‌پال
- فاکتور تولید و لینک پرداخت
- تأیید تراکنش (webhook یا polling)
- تمدید خودکار نیست (دستی)
- ثبت سابقه تراکنش‌ها

### خروجی Database
- `subscriptions` table: id, user_id, tier, start_date, end_date, is_active
- `transactions` table: id, user_id, amount, status, reference_id, created_at

### API Integrations
- Zarinpal Payment Gateway
  - `request()`: تولید لینک پرداخت
  - `verify()`: تأیید تراکنش
  - Webhook: تأیید موفق

### وابستگی
- User Management
- Route Management (با محدودیت روی تعداد کانال‌های مقصد فعال)
- Logging

### V1 / Post-V1
- V1: درگاه Zarinpal، polling برای تأیید
- Post-V1: درگاه دوم (بهم‌پرداخت)، webhook، تمدید خودکار، discount codes

---

## ۳. ماژول Route Management

### وظایف
- تعریف مسیر جدید (`/addroute`): source_channel + target_channel
- بررسی دسترسی ربات (admin in both channels)
- خواندن تمام پست‌های موجود از مبدأ
- پر کردن صف ابتدایی
- نمایش لیست مسیرها (`/listroutes`)
- حذف مسیر (`/removeroute`)
- فعال/غیرفعال موقت مسیر

### خروجی Database
- `routes` table: id, user_id, source_channel_id, target_channel_id, is_active, created_at
- `route_configs` table: id, route_id, max_posts_per_run, created_at

### وابستگی
- User Management (تعلق به کاربر)
- Subscription Management (محدود شدن تعداد کانال‌های مقصد)
- Post Queue System (صف پست‌ها)
- Logging

### V1 / Post-V1
- V1: یک مسیر = یک مبدأ به یک مقصد
- Post-V1: multiple sources to one target، multiple targets from one source

---

## ۴. ماژول Post Queue System

### وظایف
- ذخیره پست‌های قدیمی در صف (status='pending')
- مدیریت وضعیت پست (pending, sent, failed, removed)
- ترتیب ارسال: بر اساس زمان ارسال اصلی (source_date) - قدیمی‌ترین اول
- هر پست فقط یک بار ارسال شود (no duplicates)
- ثبت خطاها (last_error, retry_count)
- دستور `/updatesource`: اضافه کردن پست‌های جدید
- دستور `/sync`: همگام‌سازی و حذف پست‌های ناموجود

### خروجی Database
- `post_queue` table: id, route_id, message_id_in_source, source_date, status, retry_count, last_error, created_at

### وابستگی
- Route Management
- Execution Engine (برای اجرا)
- Logging

### V1 / Post-V1
- V1: بررسی ساده وجود پست (sync)
- Post-V1: batch operations، archive old posts

---

## ۵. ماژول Schedule System

### وظایف
- دو روش زمانبندی:
  1. **Interval Method**: start_time، end_time، interval_minutes، days_of_week
  2. **Daily Count Method**: posts_per_day، start_hour، end_hour، smart distribution
- مدیریت `next_run` (زمان اجرای بعدی)
- مدیریت `loop_mode` (one-shot یا infinite loop)
- دستور `/addplan <route_id>`: ایجاد پلان جدید
- دستور `/listplans <route_id>`: نمایش پلان‌های مسیر
- دستور `/editplan <plan_id>`: ویرایش پارامترها
- دستور `/removeplan <plan_id>`: حذف پلان
- دستور `/toggleplan <plan_id>`: فعال/غیرفعال

### خروجی Database
- `schedules` table: id, route_id, schedule_type (interval/daily_count), time_spec (JSON), posts_per_run, loop_mode, next_run, is_active, last_run
- `schedule_times` table: id, schedule_id, scheduled_time, status (pending/done) — فقط برای Daily Count method

### محاسبات
- **Interval**: next_run = now + interval_minutes
- **Daily Count**: توزیع مساوی posts_per_day در بازه start_hour تا end_hour
- اگر next_run از end_time عبور کرد، به start_time روز بعد برو

### وابستگی
- Route Management
- Post Queue System
- Execution Engine
- Logging

### V1 / Post-V1
- V1: Interval و Daily Count methods
- Post-V1: Custom time schedules، timezone support، holidays

---

## ۶. ماژول Execution Engine

### وظایف
- حلقه اجرا (while True) هر ۳۰ ثانیه
- جستجو پلان‌های فعال (`next_run <= NOW()`)
- Lock row در صف پست‌ها (SELECT FOR UPDATE)
- گرفتن اولین پست pending از صف
- ارسال پست به مقصد (forward)
- مدیریت خطا و retry (۳ بار تلاش)
- اگر صف خالی: loop_mode=true ➜ ریست و شروع دوباره، loop_mode=false ➜ پلان را غیرفعال کن
- محاسبه next_run بر اساس نوع پلان

### خروجی Database
- `logs` table: id, schedule_id, post_queue_id, status, error_message, created_at
- Update `post_queue`: status, retry_count, last_error

### وابستگی
- Schedule System
- Post Queue System
- Logging
- Rubpy Client (API روبیکا)

### Rate Limiting
- فاصله ۰.۵ ثانیه بین درخواست‌ها

### V1 / Post-V1
- V1: Async loop، 500 concurrent users، 5000 active plans
- Post-V1: Distributed execution، horizontal scaling

---

## ۷. ماژول Content Calendar

### وظایف
- دستور `/calendar <target_channel_id>`: نمایش تقویم محتوایی
- جمع‌آوری تمام پلان‌های آن مقصد
- نمایش ۳۰ روز آینده: کدام پست در کدام ساعت ارسال خواهد شد
- نمایش آخرین ۷ روز: پست‌های ارسال‌شده و وضعیت (موفق/ناموفق)
- نمایش به صورت متن یا دکمه‌های شیشه‌ای (week navigation)

### خروجی
- پیام متن فارسی با جزئیات زمان‌بندی

### وابستگی
- Schedule System
- Post Queue System
- Logging

### V1 / Post-V1
- V1: متن ساده، ۳۰ روز آینده
- Post-V1: نمودار بصری، تصادم detection، alerts

---

## ۸. ماژول Admin Dashboard

### وظایف
- صفحه داشبورد اصلی: آمار سیستم
- مدیریت کاربران
- نمایش لاگ‌ها و خطاها
- آمار عملکرد روزانه
- مشاهده وضعیت سرور و ربات
- خروجی گزارش (CSV)

### خروجی Database
- قرائتی: existing tables

### وابستگی
- User Management
- Subscription Management
- Logging
- FastAPI backend

### V1 / Post-V1
- V1: صفحات اصلی (stats, users, logs, performance)
- Post-V1: نمودارهای پیشرفته، export advanced formats، webhooks

---

## ۹. ماژول Bot Commands

### وظایف
- `/start`: ثبت‌نام/ورود، وضعیت تریال، راهنما
- `/buy`: نمایش سطوح اشتراک و لینک پرداخت
- `/addroute`: ایجاد مسیر جدید
- `/listroutes`: نمایش مسیرهای کاربر
- `/removeroute <route_id>`: حذف مسیر
- `/addplan <route_id>`: ایجاد پلان
- `/listplans <route_id>`: نمایش پلان‌های مسیر
- `/editplan <plan_id>`: ویرایش پلان
- `/removeplan <plan_id>`: حذف پلان
- `/toggleplan <plan_id>`: فعال/غیرفعال
- `/sync <route_id>`: همگام‌سازی صف
- `/updatesource <route_id>`: اضافه کردن پست‌های جدید
- `/calendar <target_channel_id>`: تقویم محتوایی
- `/logs <plan_id>`: نمایش لاگ‌های پلان
- `/help`: راهنمای کامل

### وابستگی
- تمام ماژول‌ها

### V1 / Post-V1
- V1: تمام دستورات بالا
- Post-V1: Inline keyboard patterns، state machine

---

## ۱۰. ماژول Logging & Error Handling

### وظایف
- ثبت تمام رویدادهای مهم
- مدیریت خطاهای API
- Rotating file logs (قدیمی‌ها حذف شوند)
- سطح log: INFO, ERROR, DEBUG
- ثبت retry attempts و failures

### خروجی Database
- `logs` table (همان execution engine)

### Logging Levels
- **INFO**: دستورات موفق، اجرای پلان‌ها
- **ERROR**: خطاهای retry شدن، failures
- **DEBUG**: جزئیات فنی

### وابستگی
- تمام ماژول‌ها

---

## خلاصه وابستگی‌های ماژول‌ها

```
User Management
  ↓
Subscription & Payment ← Route Management ← Post Queue System ← Schedule System ← Execution Engine ← Admin Dashboard
                                                          ↑                                              ↑
                                                    Content Calendar ←────────────────────────────────┘
```

---

## نتیجه‌گیری P2

- **۱۰ ماژول** شناسایی شده‌اند
- **وابستگی‌ها** مشخص شده‌اند
- **V1 vs Post-V1** جدا شده‌اند
- **خروجی Database** روشن است
- مراحل بعدی: **P3 - معماری فنی**
