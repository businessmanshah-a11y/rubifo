# 🧪 راهنمای تست محلی Rubifo

## ✅ وضعیت راه‌اندازی

- ✅ Database ایجاد شده
- ✅ Migrations اجرا شده
- ✅ Test data درج شده
- ✅ Dependencies نصب شده
- ⏳ ربات و Admin panel آماده برای اجرا

---

## 🚀 شروع سریع

### **گزینه 1: اجرای خودکار (توصیه شده)**

```bash
cd /Users/infinite/Desktop/rubifo
bash run_local.sh
```

### **گزینه 2: اجرای دستی**

#### Terminal 1 - ربات:
```bash
cd /Users/infinite/Desktop/rubifo
python3 -m src.bot.main
```

#### Terminal 2 - Admin Panel:
```bash
cd /Users/infinite/Desktop/rubifo
uvicorn src.admin.main:app --host 127.0.0.1 --port 8000 --reload
```

---

## 🌐 دسترسی به سرویس‌ها

### **Admin Dashboard**
- **URL**: http://127.0.0.1:8000/admin/
- **Username**: `admin`
- **Password**: (تنظیم نشده - نیاز به بروزرسانی bcrypt hash)

### **API Health Check**
```bash
curl http://127.0.0.1:8000/health
```

### **Database**
```bash
psql rubifo
```

---

## 📝 داده‌های تست

### **کاربر تست**
```sql
SELECT * FROM users;
-- user_id: 987654321
-- username: testuser
-- تریال: 48 ساعت باقی‌مانده
```

### **اشتراک تست**
```sql
SELECT * FROM subscriptions;
-- tier: basic
-- 1 مسیر مجاز
```

### **مسیر تست**
```sql
SELECT * FROM routes;
-- source: 12345
-- target: 67890
-- active: true
```

---

## 🧪 سناریوهای تست

### **سناریو 1: تست دستورات ربات (بدون Rubika)**

تمام دستورات را می‌توانید مستقیماً از API تست کنید:

```bash
# /start کاربر جدید
curl -X POST http://127.0.0.1:8000/api/bot \
  -H "Content-Type: application/json" \
  -d '{"user_id": 987654321, "text": "/start"}'

# /buy کاشتن اشتراک
curl -X POST http://127.0.0.1:8000/api/bot \
  -H "Content-Type: application/json" \
  -d '{"user_id": 987654321, "text": "/buy"}'

# /listroutes
curl -X POST http://127.0.0.1:8000/api/bot \
  -H "Content-Type: application/json" \
  -d '{"user_id": 987654321, "text": "/listroutes"}'
```

### **سناریو 2: تست Zarinpal (Sandbox)**

```bash
# درخواست پرداخت
curl -X POST https://api.zarinpal.com/pg/v4/payment/request.json \
  -H "Content-Type: application/json" \
  -d '{
    "merchant_id": "test_merchant",
    "amount": 50000,
    "description": "Test payment",
    "callback_url": "http://127.0.0.1:8000/payment/callback"
  }'
```

### **سناریو 3: تست Queue و Schedule**

```bash
# بررسی صف
psql rubifo -c "SELECT * FROM post_queue;"

# بررسی برنامه‌های اجرایی
psql rubifo -c "SELECT * FROM schedules;"

# بررسی statistics
curl http://127.0.0.1:8000/admin/stats \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

---

## 🔐 تنظیم Admin Password

### **مرحله 1: تولید bcrypt hash**

```bash
python3 << EOF
import bcrypt
password = "your_secure_password"
hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
print(hashed.decode())
EOF
```

### **مرحله 2: بروزرسانی .env**

```bash
nano .env
# جایگزین ADMIN_PASSWORD_HASH با hash جدید
```

### **مرحله 3: تولید JWT Token**

```bash
python3 << EOF
from src.admin.auth import AdminAuth
auth = AdminAuth()
token = auth.create_token("admin")
print(f"JWT Token: {token}")
EOF
```

---

## 📊 تست Dashboard مدیریتی

### **1. ورود**

```bash
curl -X POST http://127.0.0.1:8000/admin/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "your_password"
  }'
# نتیجه: {"access_token": "token_here", "token_type": "bearer"}
```

### **2. خلاصه Dashboard**

```bash
TOKEN="your_jwt_token"
curl http://127.0.0.1:8000/admin/dashboard-summary \
  -H "Authorization: Bearer $TOKEN"
```

### **3. لیست کاربران**

```bash
TOKEN="your_jwt_token"
curl http://127.0.0.1:8000/admin/users \
  -H "Authorization: Bearer $TOKEN"
```

### **4. تاریخچه تراکنش‌ها**

```bash
TOKEN="your_jwt_token"
curl http://127.0.0.1:8000/admin/transactions \
  -H "Authorization: Bearer $TOKEN"
```

### **5. مسیرها و صف**

```bash
TOKEN="your_jwt_token"
curl http://127.0.0.1:8000/admin/routes \
  -H "Authorization: Bearer $TOKEN"
```

---

## 🧪 تست‌های خودکار

### **اجرای Unit Tests**

```bash
cd /Users/infinite/Desktop/rubifo
pytest tests/test_user_service.py -v
```

### **اجرای تمام تست‌ها**

```bash
pytest tests/ -v --tb=short
```

### **تست با coverage**

```bash
pytest tests/ --cov=src --cov-report=html
open htmlcov/index.html
```

---

## 🔍 نظارت و Debugging

### **مشاهده لاگ‌های ربات**

```bash
tail -f logs/bot.log
```

### **مشاهده لاگ‌های Admin Panel**

```bash
tail -f logs/admin.log
```

### **بررسی وضعیت Database**

```bash
# تمام جداول
psql rubifo -c "\dt"

# تعداد رکورد‌ها
psql rubifo -c "
SELECT 
  'users' as table_name, COUNT(*) as count FROM users
UNION ALL
SELECT 'subscriptions', COUNT(*) FROM subscriptions
UNION ALL
SELECT 'routes', COUNT(*) FROM routes
UNION ALL
SELECT 'post_queue', COUNT(*) FROM post_queue
UNION ALL
SELECT 'schedules', COUNT(*) FROM schedules;"
```

---

## ⚠️ حل مشاکل

### **مشکل: Database Connection Error**

```bash
# بررسی PostgreSQL
psql -U postgres -c "SELECT 1"

# بررسی rubifo database
psql rubifo -c "SELECT version();"

# اعادہ‌سازی database
dropdb rubifo
createdb rubifo
psql rubifo < migrations/001_init_schema.sql
psql rubifo < migrations/002_post_and_schedule.sql
```

### **مشکل: Port 8000 Already in Use**

```bash
# پیدا کردن process استفاده‌کننده از port
lsof -i :8000

# کشتن process
kill -9 <PID>

# یا استفاده از port دیگر
uvicorn src.admin.main:app --host 127.0.0.1 --port 8001
```

### **مشکل: Import Errors**

```bash
# دوباره نصب dependencies
pip3 install -r requirements.txt --force-reinstall

# بررسی Python version
python3 --version  # باید 3.10+ باشد
```

---

## 📋 Checklist تست کامل

- [ ] Database متصل است
- [ ] Admin Panel در http://127.0.0.1:8000 اجرا می‌شود
- [ ] Swagger docs در http://127.0.0.1:8000/docs دسترس‌پذیر است
- [ ] میتوانید با /admin/login وارد شوید
- [ ] Dashboard metrics نمایش می‌دهد
- [ ] کاربران تست دیده می‌شوند
- [ ] مسیرها و صف نمایش داده می‌شوند
- [ ] Unit tests pass می‌شوند
- [ ] لاگ‌ها بدون error نوشته می‌شوند

---

## 📞 پشتیبانی و منابع

### **فایل‌های مهم**

- `.env` - تنظیمات
- `logs/` - فایل‌های لاگ
- `migrations/` - scripts بانک اطلاعات
- `src/` - کد منبع

### **مستندات**

- `DEPLOYMENT.md` - deployment در تولید
- `LAUNCH.md` - راه‌اندازی
- `PROJECT_COMPLETE.md` - خلاصه پروژه

---

**🎉 Happy Testing! برای سوالات، شروع با `logs/` شروع کنید!**
