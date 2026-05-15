# P5 و P6 - جریان کاربر، نقشه سایت و MVP Boundaries
**تاریخ:** ۱۴۰۵/۰۲/۲۵ | ۲۰۲۶/۰۵/۱۵  
**وضعیت:** ✅ تمام

---

## P5 - جریان کاربری (User Journeys)

### ۱. Journey - کاربر جدید (First Time)

```
User: /start
└─► Bot: سلام! خوش آمدید. 48 ساعت تریال رایگان فعال شد.
            دستورات:
            /buy - برای خرید اشتراک
            /help - راهنما
            /addroute - ایجاد مسیر جدید

User: /help
└─► Bot: راهنمای کامل تمام دستورات (فارسی)

User: /addroute
└─► Bot: شناسه یا @username کانال مبدأ را بفرستید.
User: @source_channel
└─► Bot: بررسی... ✅ کانال مبدأ تایید شد.
         شناسه یا @username کانال مقصد را بفرستید.
User: @target_channel
└─► Bot: بررسی... ✅ کانال مقصد تایید شد.
         مسیر ایجاد شد. Route ID: 123
         صف اولیه پر شد (50 پست کهنه موجود).
         می‌توانید اکنون با /addplan برای این مسیر پلان بسازید.

User: /addplan 123
└─► Bot: نوع زمانبندی را انتخاب کنید:
         [Interval] - هر X دقیقه یکبار
         [Daily Count] - X پست در روز

User: [Interval]
└─► Bot: ساعت شروع؟
User: 08:00
└─► Bot: ساعت پایان؟
User: 21:00
└─► Bot: فاصله زمانی (دقیقه)؟
User: 30
└─► Bot: روزهای هفته (شنبه=0، جمعه=6)؟ (اختیاری، Enter برای هر روز)
User: 0,1,2,3,4,5,6
└─► Bot: تعداد پست در هر اجرا؟
User: 1
└─► Bot: حالت Loop؟
         [one-shot] - اگر صف خالی شود، پلان متوقف شود
         [infinite] - صف از ابتدا شروع شود
User: [one-shot]
└─► Bot: ✅ پلان ایجاد شد. Plan ID: 456
         اجرای بعدی: امروز ساعت 08:00
         می‌توانید با /listplans 123 پلان‌های مسیر را ببینید.
```

### ۲. Journey - کاربر تریال انقضایی

```
Day 0: User /start
└─► Trial starts، پیام خوشامدگویی

Day 1 (24 ساعت قبل): Reminder message
└─► Bot (خودکار): "تریال شما ۲۴ ساعت دیگر تمام می‌شود.
                    برای ادامه، /buy را بفرستید."

Day 2 (تریال تمام):
└─► Bot (خودکار): "تریال شما تمام شد. تمام پلان‌ها غیرفعال شدند.
                    برای فعال‌سازی مجدد، /buy را بفرستید."

User: /buy
└─► Bot: سه سطح اشتراک:
         [Basic] ۱ مسیر - ۵۰,۰۰۰ تومان/ماه
         [Pro] ۳ مسیر - ۱۲۰,۰۰۰ تومان/ماه
         [Enterprise] ۱۰ مسیر - ۳۵۰,۰۰۰ تومان/ماه

User: [Pro]
└─► Bot: فاکتور اماده است.
         مبلغ: ۱۲۰,۰۰۰ تومان
         [پرداخت کنید]
         
User: [پرداخت کنید]
└─► Bot: (لینک پرداخت زرین‌پال)
         https://zarinpal.example/req/ABC123

User: (پرداخت موفق)
└─► Bot (خودکار پس از ۵ دقیقه): "✅ پرداخت تأیید شد!
                                  اشتراک Pro شما برای ۳۰ روز فعال شد.
                                  تمام پلان‌ها دوباره فعال شدند."
```

### ۳. Journey - مدیریت مسیرها و پلان‌ها

```
User: /listroutes
└─► Bot: مسیرهای شما:
         [Route 123] @source → @target (فعال، ۲ پلان)
         [Route 124] @another_src → @another_tgt (غیرفعال، ۰ پلان)

User: /listplans 123
└─► Bot: پلان‌های Route 123:
         [Plan 456] Interval: 8:00-21:00 هر 30 دقیقه (فعال، بعدی: امروز 10:30)
         [Plan 457] Daily: 10 پست در روز (فعال، بعدی: فردا 06:40)

User: /calendar @target_channel
└─► Bot: تقویم محتوایی برای @target_channel (۳۰ روز آینده):
         
         شنبه ۲۵ اردیبهشت:
         ۰۸:۰۰ - Route 123, Plan 456 (پست #1)
         ۰۸:۳۰ - Route 123, Plan 456 (پست #2)
         ...
         
         تعداد پست امروز: ۸ پست
         تعداد پست فردا: ۱۲ پست

User: /toggleplan 456
└─► Bot: ✅ Plan 456 غیرفعال شد.
         برای فعال‌سازی دوباره: /toggleplan 456

User: /sync 123
└─► Bot: ✅ همگام‌سازی آغاز شد...
         تعداد پست‌های حذف‌شده: 3
         تعداد پست‌های باقی‌مانده: 47

User: /updatesource 123
└─► Bot: ✅ به‌روزرسانی آغاز شد...
         تعداد پست‌های جدید: 5
         صف فعلی: 52 پست
```

### ۴. Journey - Dashboard Admin

```
Admin: Opens dashboard at /admin
└─► Login page

Admin: (username + password)
└─► Dashboard with:
    - Total users: 152
    - Active subscriptions: 89
    - Total routes: 234
    - Active plans: 567
    - Messages forwarded today: 12,345
    
    Chart: Messages per day (last 7 days)
    Chart: Subscription distribution (pie)
    
Admin: (Clicks on Users tab)
└─► User list with search/filter
    Columns: User ID, Username, Subscription, Trial End, Active Routes, Last Activity
    Actions: Message, Extend subscription, Disable user, View details
    
Admin: (Clicks on message icon for user 123)
└─► Modal: "Send message to user 123"
    Input: "Your plan will be renewed on 2026-06-15"
    [Send] button
    
└─► Bot (خودکار): "📢 پیام از پشتیبانی: Your plan will be renewed on 2026-06-15"

Admin: (Logs tab)
└─► Filter by date, user, plan, error level
    Recent logs:
    - 14:35 SUCCESS Plan 456 executed, 1 message sent
    - 14:32 RETRY Plan 789, attempt 2/3, error: "Channel not found"
    - 14:30 ERROR Plan 123 deactivated: "Bot not admin in target channel"
```

---

## P6 - MVP Boundaries و Scope Decisions

### خروجی V1 - آنچه که شامل است

#### ۱. User Management
- ✅ ثبت‌نام (`/start`)
- ✅ 48-hour trial for all new users
- ✅ Trial reminder at 24h before end
- ✅ User status: trial / active / inactive

#### ۲. Subscription & Payment
- ✅ 3 tiers: Basic (1 route, 50K), Pro (3 routes, 120K), Enterprise (10 routes, 350K)
- ✅ Zarinpal integration (request + verify)
- ✅ Invoice generation
- ✅ Polling for transaction verification (every 10 sec, 5 min timeout)
- ✅ Transaction history DB
- ✅ Manual renewal (no auto-renewal in V1)

#### ۳. Route Management
- ✅ Create route with `/addroute` (channel ID or @username)
- ✅ Bot permission check (admin in both channels)
- ✅ Initial queue population (read all existing posts)
- ✅ List routes (`/listroutes`)
- ✅ Delete route (`/removeroute`)
- ✅ Enforce subscription tier limits

#### ۴. Post Queue System
- ✅ Post queue with status: pending, sent, failed, removed
- ✅ Ordered by source_date (oldest first)
- ✅ No duplicates (one-time forward only)
- ✅ Error logging and retry count
- ✅ `/updatesource` - add new posts to end of queue
- ✅ `/sync` - remove deleted posts from queue

#### ۵. Schedule System
- ✅ Interval method: start_time, end_time, interval_minutes, days_of_week
- ✅ Daily count method: posts_per_day, start_hour, end_hour, smart distribution
- ✅ `next_run` calculation and management
- ✅ `loop_mode`: one-shot vs infinite loop
- ✅ `/addplan`, `/listplans`, `/editplan`, `/removeplan`, `/toggleplan`

#### ۶. Execution Engine
- ✅ 30-second loop checking `next_run <= NOW()`
- ✅ Row-level locking (SELECT FOR UPDATE)
- ✅ Forward message to target channel
- ✅ Retry up to 3 times with 5-minute delay
- ✅ Mark as sent/failed
- ✅ Queue reset for loop_mode=true
- ✅ Plan deactivation for loop_mode=false when queue empty

#### ۷. Content Calendar
- ✅ `/calendar <target_channel_id>` command
- ✅ Display scheduled posts for 30 days ahead
- ✅ Show past 7 days with delivery status
- ✅ Text-based display with week navigation buttons

#### ۸. Bot Commands & UX
- ✅ All 14 commands with Farsi text and step-by-step prompts
- ✅ Inline keyboards (one-shot/loop selection، etc.)
- ✅ User-friendly error messages in Farsi
- ✅ Help menu (`/help`)

#### ۹. Logging & Error Handling
- ✅ Rotating logs (cleanup old logs)
- ✅ Log levels: INFO, ERROR, DEBUG
- ✅ Error tracking: retry_count, last_error
- ✅ Bot deactivation on critical errors (not admin، channel missing، etc.)

#### ۱۰. Admin Dashboard
- ✅ Stats page: user count, active subs, routes, plans, messages forwarded
- ✅ User management: list، filter، message، extend subscription، disable
- ✅ Logs page: search، filter by date/user/plan/level
- ✅ Performance: messages per hour/day، error count، queue status
- ✅ Settings: bot token validation، trial enable/disable

---

### خروجی POST-V1 - آنچه که نیست

#### ❌ Not in V1
- ❌ **Social authentication** (Google، Telegram login) → Later
- ❌ **Two-factor authentication** → Later
- ❌ **Multiple payment gateways** (Only Zarinpal in V1) → Later
- ❌ **Auto-renewal** (Manual only in V1) → Later
- ❌ **Webhook verification** from Zarinpal (Polling only) → Later
- ❌ **Rate limiting** per user → Later
- ❌ **Discount codes / Coupons** → Later
- ❌ **API for third-party apps** → Later
- ❌ **Distributed execution** (single bot instance) → Later
- ❌ **Advanced monitoring** (Sentry integration) → Later
- ❌ **Mobile app** → Later
- ❌ **Channel scheduling** (publish at specific time) → Later
- ❌ **Message templates** → Later
- ❌ **Backup & restore** → Later
- ❌ **Bulk operations** → Later
- ❌ **Custom webhooks** → Later

---

### تصمیم‌های حذف/تعویق

#### ۱. **Interactive Trust Map** (اختیاری سابقاً)
- **تصمیم**: حذف شده در V1
- **دلیل**: UI پیچیده برای Telegram، اعتمادسازی از راهای دیگر (مقالات، پروژه‌ها)

#### ۲. **CRM و Lead Management** (سابقاً در نظر گرفته شده)
- **تصمیم**: تعویق برای بعدی
- **دلیل**: Rubifo فقط فوروارد کننده است، نه CRM

#### ۳. **3D Visualization** (سابقاً)
- **تصمیم**: حذف
- **دلیل**: خارج از scope ربات متنی

#### ۴. **GraphQL API**
- **تصمیم**: تعویق، V1 فقط REST
- **دلیل**: Complexity unnecessary for MVP

#### ۵. **Multiple Bot Instances** (Clustering)
- **تصمیم**: یک instance در V1
- **دلیل**: 500 users و 5000 plans کافی برای یک instance

---

### Scope Constraints

#### محدودیت‌های V1

| محدودیت | مقدار | دلیل |
|--------|--------|--------|
| Max users | 500 | یک instance |
| Max routes per user | 1 (Basic) - 10 (Enterprise) | Design محدود |
| Max plans | نامحدود | فنی مشکلی نیست |
| Queue size | unlimited | PostgreSQL handles |
| Retry attempts | 3 times | Reasonable default |
| Retry delay | 5 minutes | User-friendly |
| API rate limit | 0.5 sec between calls | Rubika API |
| Execution loop | every 30 sec | Good balance |

---

### Definition of Done - MVP

✅ User management (trial + subscription)  
✅ Route & queue system working  
✅ Both scheduling methods (interval + daily count)  
✅ Execution engine with retry logic  
✅ Zarinpal payment integration  
✅ Content calendar  
✅ Admin dashboard  
✅ All commands working  
✅ Logging & error handling  
✅ Farsi UI complete  
✅ Documentation complete  
✅ Database schema migrations  
✅ Docker setup  
✅ Local + staging + production ready  

---

## نتیجه‌گیری P5 & P6

✅ تمام user journeys مشخص شده‌اند  
✅ Admin dashboard flows تعریف شده‌اند  
✅ V1 scope واضح و محدود است  
✅ Post-V1 features برای بعدی جدا شده‌اند  
✅ Constraints و limits مشخص هستند  

**مراحل بعدی:**  
- P7: WBS و Milestones (تقسیم به tasks)
- P8: دستورالعمل‌های AI (CLAUDE.md، AGENTS.md)
- P9: چک‌لیست‌های دیپلوی و محتوا

