# Web Registration & Bot Linking — Design Spec

**Date:** 2026-06-07  
**Status:** Approved  
**Scope:** ثبت‌نام کاربر از طریق سایت + لینک شدن به ربات روبیکا

---

## Context

تا قبل از این تغییر، تنها مسیر ثبت‌نام از طریق ربات روبیکا بود:
کاربر `/start` می‌زد → شماره می‌داد → رمز می‌ساخت → می‌تونست وارد سایت بشه.

درگاه پرداخت زیبال نیاز داشت که کاربر بتونه مستقیم از سایت ثبت‌نام کنه و پلن بخره.  
هدف: مسیر موازی ثبت‌نام از سایت بدون شکستن هیچ‌چیز از سیستم فعلی.

---

## تصمیم معماری — رویکرد B: ستون `rubika_user_id` جداگانه

کاربران سایتی یک `user_id` ثابت مصنوعی (`web_<uuid>`) می‌گیرن که **هیچ‌وقت تغییر نمی‌کنه**.  
موقع لینک ربات، فقط ستون `rubika_user_id` ست می‌شه.

**مزایا:**
- JWT کاربر بعد از لینک ربات همچنان valid می‌مونه
- هیچ FK در جداول دیگه نیاز به آپدیت نداره
- کاربران قدیمی ربات کاملاً بی‌تأثیر می‌مونن

---

## ۱. تغییر Schema — Migration 013

```sql
ALTER TABLE users ADD COLUMN rubika_user_id TEXT UNIQUE;

-- کاربران قدیمی ربات: rubika_user_id = user_id
UPDATE users SET rubika_user_id = user_id
WHERE user_id NOT LIKE 'web_%';
```

**حالت‌های رکورد کاربر:**

| نوع کاربر | `user_id` | `rubika_user_id` | `is_trial_active` |
|-----------|-----------|------------------|-------------------|
| ربات (قدیمی) | `b0HRK4...` | `b0HRK4...` | طبق منطق فعلی |
| سایت (قبل لینک) | `web_a3f9c2...` | `NULL` | `False` |
| سایت (بعد لینک) | `web_a3f9c2...` | `b0HRK4...` | `True` |

**نکته تریال:** برای کاربران سایتی تریال **از لحظه لینک شدن ربات** شروع می‌شه، نه ثبت‌نام.

---

## ۲. ثبت‌نام وب — Endpoint جدید

```
POST /api/auth/register
Content-Type: application/json

{
  "phone_number": "09123456789",
  "password": "mypassword",
  "confirm_password": "mypassword"
}
```

**Validations:**
- فرمت شماره: `^09\d{9}$`
- رمز: حداقل ۶ کاراکتر
- `password == confirm_password`
- شماره قبلاً در DB نباشه

**اقدام:**
```python
user_id = "web_" + secrets.token_hex(12)
# UserService.create_web_user(phone, password)
# → INSERT users(user_id, phone_number, password_hash, is_trial_active=False)
# Return JWT (sub = user_id) + user data
```

**Response موفق:** `{ access_token, token_type: "bearer", user: {...} }`  
**Response خطا:** `{ detail: "این شماره قبلاً ثبت‌نام کرده" }` با کد 409

---

## ۳. UI — صفحه `/login` با دو تب

صفحه `/login` فعلی به دو تب تبدیل می‌شه:

- **تب «ورود»** (پیش‌فرض فعال): فرم فعلی — شماره + رمز
- **تب «ثبت‌نام»**: شماره + رمز + تکرار رمز + دکمه «ساخت حساب و شروع»

بعد از ثبت‌نام موفق: ری‌دایرکت به `/plans` (یا `next` param اگه وجود داشت).

---

## ۴. تغییرات `UserService`

**متد جدید: `create_web_user(phone, password)`**
```python
async def create_web_user(self, phone: str, password: str) -> User:
    """Create user from web registration — no Rubika GUID yet."""
    user_id = "web_" + secrets.token_hex(12)
    normalized = self.normalize_phone(phone)
    hashed = self.hash_password(password)
    # INSERT INTO users(user_id, phone_number, password_hash, is_trial_active)
    # VALUES($1, $2, $3, FALSE)
```

**متد جدید: `link_rubika_account(web_user_id, rubika_guid)`**
```python
async def link_rubika_account(self, web_user_id: str, rubika_guid: str) -> User:
    """Link a web-registered user to their Rubika bot account. Starts trial."""
    # UPDATE users SET
    #   rubika_user_id = $rubika_guid,
    #   is_trial_active = TRUE,
    #   trial_start_at = NOW(),
    #   trial_end_at = NOW() + INTERVAL '72 hours'
    # WHERE user_id = $web_user_id
```

**تغییر متد `get_or_create_user(rubika_guid, username)`:**
```python
# اول چک rubika_user_id
user = await self.get_user_by_rubika_id(rubika_guid)
if user: return user
# بعد چک user_id (کاربران قدیمی ربات)
user = await self.get_user(rubika_guid)
if user: return user
# کاربر کاملاً جدید
return await self._create_bot_user(rubika_guid, username)
```

**متد جدید: `get_user_by_rubika_id(rubika_guid)`**
```sql
SELECT * FROM users WHERE rubika_user_id = $1
```

---

## ۵. جریان لینک ربات (Bot Linking Flow)

وقتی کاربر سایتی ربات رو باز می‌کنه:

```
/start دریافت می‌شه
    ↓
get_or_create_user(rubika_guid)
    → پیدا نشد → ادامه onboarding
    ↓
state: web_onboarding_phone
ربات شماره می‌خواد
    ↓
handle_web_onboarding_phone(phone):
    existing = get_user_by_phone(phone)

    حالت ۱: existing نیست
        → کاربر جدید کامل → ادامه معمولی (رمز بساز)

    حالت ۲: existing هست + rubika_user_id IS NULL
        → کاربر سایتی → state: web_linking_password_verify
        → ربات: «این شماره حساب سایتی داره. رمزت رو وارد کن:»

    حالت ۳: existing هست + rubika_user_id IS NOT NULL
        → تداخل → «این شماره به حساب دیگه‌ای لینکه، شماره دیگه‌ای وارد کن»

    ↓ (حالت ۲)
handle_web_linking_password_verify(password):
    verify_password(password, existing.password_hash)

    اشتباه (تا ۳ بار):
        → «رمز اشتباهه. دوباره امتحان کن.»
        → بعد ۳ بار: state reset

    درست:
        → link_rubika_account(existing.user_id, rubika_guid)
        → «✅ حسابت با شماره 09... به ربات وصل شد! تریال ۷۲ ساعته شروع شد.»
        → منوی اصلی
```

---

## ۶. State جدید ربات

در `conversation_state` (یا هر جایی که state نگه داشته می‌شه):

| State | توضیح |
|-------|-------|
| `web_onboarding_phone` | موجود — انتظار شماره |
| `web_onboarding_password` | موجود — انتظار رمز جدید (کاربر جدید) |
| `web_linking_password_verify` | **جدید** — انتظار رمز تأیید مالکیت |

همچنین یه counter برای تعداد تلاش اشتباه رمز:  
`linking_attempts: int` — بعد از ۳ بار اشتباه، state کاملاً ریست می‌شه.

---

## ۷. امنیت

| تهدید | محافظت |
|--------|--------|
| یکی با شماره دیگری ربات وصل کنه | تأیید رمز قبل از لینک |
| Brute force رمز در ربات | محدودیت ۳ بار اشتباه + state reset |
| ثبت‌نام با شماره دیگران در سایت | چک یونیق بودن phone در DB |
| JWT کاربر بعد لینک invalid بشه | user_id ثابت، فقط rubika_user_id اضافه می‌شه |

---

## ۸. فایل‌های تغییر می‌کنن

| فایل | تغییر |
|------|-------|
| `migrations/013_add_rubika_user_id.sql` | جدید — ADD COLUMN |
| `src/core/user_service.py` | متدهای `create_web_user`, `link_rubika_account`, `get_user_by_rubika_id`, آپدیت `get_or_create_user` |
| `src/bot/commands.py` | `handle_web_onboarding_phone` آپدیت + `handle_web_linking_password_verify` جدید |
| `app.py` | endpoint جدید `POST /api/auth/register` + آپدیت صفحه login |

---

## ۹. تست‌ها

- ثبت‌نام سایت با شماره جدید → JWT دریافت می‌شه
- ثبت‌نام سایت با شماره تکراری → 409
- کاربر سایتی ربات باز می‌کنه، شماره می‌ده، رمز درست → لینک + تریال شروع
- کاربر سایتی ربات باز می‌کنه، شماره می‌ده، رمز اشتباه ۳ بار → state reset
- کاربر قدیمی ربات → هیچ تغییری
- JWT کاربر سایتی بعد از لینک → همچنان valid
