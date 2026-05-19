---
name: bot-ui-redesign-2026-05-19
description: Destination-Centric UI redesign for Rubifo bot - organize keypad, inline buttons, and flows around destination channels
metadata:
  type: project
---

# Bot UI Redesign: Destination-Centric Architecture
**تاریخ:** ۱۴۰۵/۰۲/۲۹ (۲۰۲۶-۰۵-۱۹)  
**موضوع:** طراحی مجدد رابط کاربری ربات بر اساس کانال‌های مقصد

---

## مسائل فعلی

۱. **منوی پایین (Keypad) بیش‌ازحد پر است**
   - ۸ دکمه در ۴ ردیف
   - دکمه‌های کم‌استفاده (مثل `/buy`) کنار دکمه‌های روزمره (مثل `/calendar`)
   - نیست هیچ تمایز بین setup و daily workflow

۲. **بدون context-sensitive actions**
   - هنگام دیدن لیست سرس‌ها، کاربر نمی‌تونه درون‌جا (`/addpost`) انجام بده
   - باید بیرون از flow برگرده

۳. **محدودیت کانال‌های مقصد نامفهوم است**
   - کاربر وقتی مسیر جدید می‌سازه برای کانال تکراری، پیام خطا می‌گیره
   - Basic: ۱ کانال مقصد (اما کاربر فکر می‌کنه ۱ مسیر)
   - Pro: ۳ کانال مقصد
   - Enterprise: ۱۰ کانال مقصد

۴. **Workflow مشخص نیست**
   - کاربر هر روز نیاز داره: calendar چک کنه → sources اپدیت کنه → posts اضافه کنه
   - اما رابط برای این flow بهینه نشده

---

## اصول طراحی

### ۱. Destination-Centric Model
- **کانال‌های مقصد** اساس منطق است (محدود‌شده توسط tier)
- هر کانال می‌تونه چندین مسیر داشته باشه (از سرس‌های مختلف)
- هر مسیر می‌تونه چندین پلن داشته باشه (schedule مختلف)

**Hierarchy:**
```
DESTINATION CHANNEL (limited by tier)
├─ Route 1: Source_A → Channel
│  ├─ Plan 1
│  └─ Plan 2
├─ Route 2: Source_B → Channel
│  └─ Plan 3
└─ Route 3: Source_C → Channel
   └─ Plan 4
```

### ۲. Setup vs Daily
- **Setup (یک‌بار):** کانال‌های مقصد رو تایید کنه، admin verification
- **بعدش forget:** کانال‌ها trust شده‌اند، دوباره نگاه نکنه
- **Daily:** calendar → sources → add posts → پلن‌ها

### ۳. Context-Sensitive Actions
- inline buttons زیر پیام برای immediate actions
- نیاز نیست کاربر برگرده menu، جستجو کنه

### ۴. Clarity on Limits
- واضح نشون بده: "شما ۲/۳ کانال استفاده کردید"
- وقتی حد رسید، clear message و upgrade option

---

## طراحی

### الف: Main Keypad (منوی پایین)

```
[📦 سورس‌های من]  [📍 کانال‌های من]  [📋 مسیرهای من]
[📅 پلن‌های من]   [📊 تقویم محتوایی]  [💳 اشتراک]
[❓ راهنما]
```

**تعریف هر دکمه:**

| دکمه | Command | Purpose | Frequency |
|------|---------|---------|-----------|
| 📦 سورس‌های من | `/mysources` | لیست سرس‌ها + inline `[➕ افزودن پست]` | روزانه |
| 📍 کانال‌های من | `/my_destinations` | لیست کانال‌های تایید‌شده + inline hub | setup/مدیریت |
| 📋 مسیرهای من | `/listroutes` | لیست مسیرها grouped by destination | هفتگی |
| 📅 پلن‌های من | `/listplans` | لیست پلن‌ها grouped by destination | هفتگی |
| 📊 تقویم محتوایی | `/calendar` | Select channel → calendar 30 روز آینده | روزانه |
| 💳 اشتراک | `/subscription_status` | Status + days left + renew/upgrade | هفتگی |
| ❓ راهنما | `/help` | دستورات و راهنما | نادر |

**شش‌ دکمه بجای هشت:**
- ❌ حذف `✏️ سورس جدید` → موج inline `[✏️ سورس جدید]` در `/mysources`
- ❌ حذف `➕ مسیر جدید` → موج inline برای هر کانال در `/my_destinations`

---

### ب: Per-Destination Hub (Inline Buttons)

وقتی کاربر `/my_destinations` یا `/listroutes` یا `/calendar` زنه:

```
کانال مقصد: @target_channel_A
Status: ✅ تایید‌شده

📋 مسیرهای این کانال: 2
  [نمایش مسیرها]

📅 پلن‌های این کانال: 3
  [نمایش پلن‌ها]

📊 تقویم این کانال
  [مشاهده تقویم]

ساختن مسیر جدید برای این کانال:
  [➕ مسیر جدید] (Source: انتخاب سرس → این کانال)

مدیریت کانال:
  [نام/توضیح] [🗑️ حذف]
```

**Inline buttons:**
- `[نمایش مسیرها]` → لیست Route #۱, #۲ با [✏️ ویرایش] [🗑️ حذف]
- `[نمایش پلن‌ها]` → لیست Plan #۱, #۲, #۳ با [✏️ ویرایش] [🗑️ حذف]
- `[مشاهده تقویم]` → calendar این کانال (۳۰ روز)
- `[➕ مسیر جدید]` → multi-step: انتخاب سرس → confirm
- `[نام/توضیح]` → اپدیت metadata کانال
- `[🗑️ حذف]` → تایید حذف (نیاز admin check)

---

### ج: Daily Workflows

#### **Workflow ۱: تقویم محتوایی (صبح هر روز)**

```
User: /calendar
Bot: 📊 کدوم کانال؟
     [۱️⃣ @channel_A] [۲️⃣ @channel_B] [۳️⃣ @channel_C]

User: @channel_A
Bot: 📊 تقویم @channel_A — ۳۰ روز آینده

     شنبه ۲۵ اردیبهشت:
     ۰۸:۰۰ — Route #1 (Source: تبلیغات) | Plan #1
     ۱۰:۰۰ — Route #2 (Source: خبرها) | Plan #2
     ۱۲:۳۰ — Route #3 (Source: محتوا) | Plan #3
     
     یکشنبه ۲۶ اردیبهشت:
     ۰۹:۰۰ — Route #1 (Source: تبلیغات) | Plan #1
     ...
     
     [◀️ هفته قبل] [هفته بعد ▶️]
     [📝 مسیرهای این کانال] [➕ مسیر جدید]
```

**نکات:**
- کاربر می‌بینه دقیقاً چی داره می‌یاد
- می‌تونه بفهمه: کدوم سرس‌ها کافی هستند، کدوم نیاز دارند
- inline action برای مسیر جدید

---

#### **Workflow ۲: مدیریت سرس‌ها (روزانه)**

```
User: /mysources
Bot: 📦 سرس‌های شما — ۳ سرس:

     #1 تبلیغات (۲۵ پست)
        متصل: Route #1 → @channel_A, Route #2 → @channel_B
        [مشاهده پست‌ها] [➕ افزودن پست] [✏️ ویرایش]
     
     #2 خبرها (۱۲ پست)
        متصل: Route #2 → @channel_A
        [مشاهده پست‌ها] [➕ افزودن پست] [✏️ ویرایش]
     
     #3 محتوای عمومی (۴۸ پست)
        متصل: Route #3 → @channel_A
        [مشاهده پست‌ها] [➕ افزودن پست] [✏️ ویرایش]
     
     [✏️ سورس جدید]
```

**نکات:**
- هر سرس نشون می‌ده کجا متصل هست (routing transparency)
- `[➕ افزودن پست]` inline است — نیاز به `/addpost [id]` نیست
- کاربر می‌تونه از اینجا محتوا مدیریت کنه

---

#### **Workflow ۳: Routes (کم‌تر مورد استفاده)**

```
User: /listroutes
Bot: 📋 مسیرهای شما:

     کانال @channel_A:
     ├─ مسیر #1: تبلیغات → @channel_A
     │  پلن‌ها: ۲ (Plan #1, #2)
     │  صف: ۲۵ پست بعدی
     │  [📅 پلن‌ها] [✏️ ویرایش] [🗑️ حذف]
     │
     └─ مسیر #2: خبرها → @channel_A
        پلن‌ها: ۱ (Plan #2)
        صف: ۱۲ پست بعدی
        [📅 پلن‌ها] [✏️ ویرایش] [🗑️ حذف]
     
     کانال @channel_B:
     └─ مسیر #3: تبلیغات → @channel_B
        پلن‌ها: ۱ (Plan #3)
        صف: ۲۵ پست بعدی
        [📅 پلن‌ها] [✏️ ویرایش] [🗑️ حذف]
```

**نکات:**
- Grouped by destination
- هر مسیر نشون می‌ده: چند پلن، چند پست در صف
- inline actions

---

### د: Subscription Status

```
User: /subscription_status
Bot: 💳 وضعیت اشتراک شما

     ✅ Pro (۳ کانال مقصد)
     تاریخ پایان: ۱۴۰۵/۰۳/۲۵
     ⏳ ۶ روز مانده
     
     کانال‌های استفاده‌شده: ۲/۳
     ✅ @channel_A
     ✅ @channel_B
     ➕ (یک کانال دیگر می‌تونی اضافه کنی)
     
     [🔄 تمدید Pro] [⬆️ ارتقا به Enterprise]
```

**یا اگر منقضی:**
```
Bot: ⚠️ اشتراک منقضی‌شده

     تریال شما ۴۸ ساعت دیگر تمام می‌شود.
     بعد از آن، تمام پلن‌ها غیرفعال می‌شوند.
     
     [💳 خرید Basic] [💳 خرید Pro] [💳 خرید Enterprise]
```

**نکات:**
- نشون بده چند کانال استفاده شده (awareness)
- رنگ‌های مختلف برای available vs used vs full

---

### ه: Validation & Error Handling

#### **Destination Channel Limit Check**

```
User: می‌خواهد مسیر جدید ایجاد کند → @channel_C
System: بررسی tier limits
Bot: ❌ محدودیت پلن Basic شما:

     شما فقط ۱ کانال مقصد می‌توانید داشته باشید.
     
     کانال‌های فعلی شما:
     ✅ @channel_A (۲ مسیر، ۳ پلن)
     
     برای اضافه کردن @channel_C:
     [⬆️ ارتقا به Pro — ۳ کانال]
     [⬆️ ارتقا به Enterprise — ۱۰ کانال]
```

**نکات:**
- واضح و clear
- inline upgrade option

#### **Admin Verification for Destination**

```
User: /my_destinations (ساخت destination جدید)
Bot: 🔐 تایید admin در @new_channel:

     ربات @Rubifo باید ادمین این کانال باشد.
     
     لطفاً این لینک را باز کنید:
     https://rubika.ir/new_channel
     
     ربات @Rubifo را ادمین کنید، سپس:
     [✅ تایید شد]
```

---

## Implementation Details

### Database Changes
- نیاز نیست schema تغییر کنه
- فقط query logic برای `my_destinations` جدید
- View برای `per_destination_stats` (routes, plans, pending posts)

### API/Rubika Endpoints
```
GET /botapi/methods → sendMessage, sendFile (existing)
POST /botapi/group-channel → Admin check (existing, enhance usage)
```

**Reference:**
- https://rubika.ir/botapi/methods
- https://rubika.ir/botapi/models
- https://rubika.ir/botapi/group-channel

### Code Changes Required

**File: `src/bot/main.py`**
- Update `MAIN_KEYPAD` (remove 2 buttons, restructure 3x2+1)

**File: `src/bot/commands.py`**
- Add `handle_my_destinations()` (new)
- Add `handle_subscription_status()` (new — replaces part of `/buy`)
- Add `handle_calendar_select()` (modify existing)
- Enhance inline button generation

**File: `src/bot/handlers.py`**
- Add routes for new commands

**File: `src/core/route_service.py`**
- Add validation: `can_create_route()` checks destination channel limit (not route count)
- Add `get_destinations_by_user()` (new)

**File: `src/core/subscription_service.py`**
- Add `get_subscription_status()` (returns status + days left + destinations used)

---

## Testing Strategy

### Unit Tests
```python
# Test: Destination limit validation
assert can_create_route(user_id=123, target="@channel_A") → True (first channel)
assert can_create_route(user_id=123, target="@channel_A") → True (same channel, different source)
assert can_create_route(user_id=123, target="@channel_B") → False (tier Basic allows 1 only)

# Test: Subscription status
status = get_subscription_status(user_id=123)
assert status.tier == "pro"
assert status.destinations_used == 2
assert status.destinations_limit == 3
```

### Integration Tests
- `/my_destinations` → verify list shows only unique channels
- Destination selection flow → `/calendar` → inline buttons work
- Adding route to existing destination → passes validation
- Upgrade flow → user can add new destination after upgrading

---

## Success Criteria

✅ Keypad reduced to ۷ durable buttons (۶ data + ۱ help)  
✅ Daily workflow clear: calendar → sources → add posts  
✅ Destination channel limits enforced & communicated clearly  
✅ Inline buttons work for immediate actions (no context-switching)  
✅ Per-destination hub groups related data (routes, plans, calendar)  
✅ Subscription status is transparent (days left, channels used/limit)  
✅ All commands updated to work with new model  
✅ Database queries optimized for per-destination grouping  

---

## Timeline

- **Phase 1 (Current):** Design & planning (this doc)
- **Phase 2:** Implementation (rewrite commands + handlers)
- **Phase 3:** Testing (unit + integration)
- **Phase 4:** Deployment

---

## References

- CLAUDE.md (Project guidelines)
- P5-user-journey-and-scope.md (User flows)
- https://rubika.ir/botapi/methods
- https://rubika.ir/botapi/models
- https://rubika.ir/botapi/group-channel
