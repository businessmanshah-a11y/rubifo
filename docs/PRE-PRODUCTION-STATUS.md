# وضعیت پیش‌تولید Rubifo
**تاریخ به‌روزرسانی:** ۱۴۰۵/۰۲/۲۵ | ۲۰۲۶/۰۵/۱۵  
**وضعیت کلی:** ✅ PRE-PRODUCTION COMPLETE - READY FOR EXECUTION

---

## خلاصه مراحل تکمیل‌شده

### ✅ P0 - SSOT آماده
- Docs folder ایجاد شده
- تمام اسناد در Git موجود
- منبع حقیقت واحد تعیین شده

### ✅ P1 - تعریف محصول (PRD)
- **فایل**: `docs/PRD.md`
- **محتوا**: نیازمندی‌های کامل در ۱۵ بخش
- **اهداف**: واضح و محدود برای V1
- **KPIs**: 500 کاربر، 5000 پلان

### ✅ P2 - تفکیک ماژول‌ها
- **فایل**: `docs/P2-feature-modules-breakdown.md`
- **ماژول‌ها**: ۱۰ ماژول تعریف‌شده
- **وابستگی‌ها**: مشخص و نقشه‌برداری‌شده
- **V1/Post-V1**: جدا‌شده

### ✅ P3 - معماری فنی
- **فایل**: `docs/P3-technical-architecture.md`
- **Stack**: Python 3.10 + Rubpy + PostgreSQL + FastAPI
- **Folder Structure**: کامل و توضیح‌شده
- **Database Schema**: ۷ جدول اصلی
- **Async Model**: 30-second execution loop
- **DevOps**: Docker + systemd

### ✅ P5 - جریان کاربری
- **فایل**: `docs/P5-user-journey-and-scope.md`
- **User Journeys**: ۴ سناریو کامل
- **Admin Flows**: تمام workflows
- **Requirements**: دقیق و قابل‌اجرا

### ✅ P6 - MVP Boundaries
- **فایل**: `docs/P5-user-journey-and-scope.md` (بخش دوم)
- **V1 Features**: ۴۰+ فیچر تعریف‌شده
- **Post-V1**: ۱۵ فیچر برای بعدی
- **Definition of Done**: مشخص

### ✅ P7 - WBS & Milestones
- **فایل**: `docs/P7-WBS-and-milestones.md`
- **Milestones**: ۸ مرحله (M0-M8)
- **Tasks**: ۷۵ task تفصیلی
- **Duration**: ~25-27 روز (موازی)
- **Dependencies**: کامل مشخص

### ⏳ P8 - دستورالعمل‌های AI
- **Status**: آماده برای ایجاد
- **Contents**: 
  - CLAUDE.md - تعلیمات Claude
  - AGENTS.md - تعلیمات agents
  - Task tracking system

### ⏳ P9 - چک‌لیست‌های Deployment
- **Status**: آماده برای ایجاد
- **Contents**:
  - Deploy checklist (local/staging/prod)
  - Content checklist

---

## مسئله‌ای که حل شده است

| سوال | جواب | منبع |
|------|------|--------|
| محصول دقیقاً چی است؟ | ربات فوروارد خودکار برای روبیکا | PRD |
| کیا ماژول‌های اصلی هستند؟ | ۱۰ ماژول مشخص شده | P2 |
| معماری فنی چطور؟ | Python + PostgreSQL + FastAPI | P3 |
| چه زمانی رسم می‌شود؟ | ~25-27 روز | P7 |
| کدام فیچر در V1 است؟ | ۴۰+ فیچر | P6 |
| کدام خارج از V1؟ | ۱۵ فیچر post-V1 | P6 |
| کاربر چطور از آن استفاده می‌کند؟ | ۴ user journey | P5 |

---

## Definition of Done - Pre-Production

### Checklist Completion

- ✅ PRD کامل و قابل‌ارجاع
- ✅ ۱۰ ماژول شناسایی‌شده
- ✅ معماری انتخاب‌شده (Python + Rubpy + PostgreSQL)
- ✅ Folder structure طراحی‌شده
- ✅ Database schema تعریف‌شده
- ✅ Async model انتخاب‌شده
- ✅ ۴ user journey تعریف‌شده
- ✅ V1 vs Post-V1 جدا‌شده
- ✅ ۷۵ task توضیح‌شده
- ✅ وابستگی‌های task مشخص
- ✅ Milestones تعریف‌شده
- ✅ Scope constraints مشخص
- ✅ Admin dashboard طراحی‌شده
- ✅ Testing strategy مشخص

### Knowledge Base

تمام اطلاعات در قسمت `docs/`:
```
docs/
├── PRD.md (1000+ سطر)
├── P2-feature-modules-breakdown.md (250+ سطر)
├── P3-technical-architecture.md (600+ سطر)
├── P5-user-journey-and-scope.md (500+ سطر)
├── P7-WBS-and-milestones.md (1000+ سطر)
├── pre-production-roadmap.md
└── PRE-PRODUCTION-STATUS.md (این فایل)
```

**جمع**: ~4000 سطر documentation

---

## اطلاعات کلیدی برای اجرا

### Stack Selection
```yaml
Language: Python 3.10+
Bot Framework: Rubpy (async)
Database: PostgreSQL
ORM: asyncpg (raw SQL + transactions)
Async Framework: asyncio
Admin Backend: FastAPI
Admin Frontend: HTML/CSS/JS + Alpine.js
DevOps: Docker + systemd
```

### Critical Numbers
- **Max Users**: 500
- **Max Plans**: 5000 active
- **Max Routes per User**: 1-10 (tier-dependent)
- **Execution Loop**: every 30 seconds
- **Retry Attempts**: 3 times
- **API Delay**: 0.5 seconds between calls

### Database Tables
```sql
users, subscriptions, transactions, routes, post_queue, 
schedules, schedule_times, logs
```

### API Endpoints (Admin)
```
/admin/login
/admin/dashboard/stats
/admin/users (GET, list)
/admin/users/{id} (GET, details)
/admin/users/{id}/message (POST)
/admin/logs (GET)
/admin/performance (GET)
/admin/transactions (GET)
```

### Bot Commands
```
/start, /help, /buy, /addroute, /listroutes, /removeroute,
/addplan, /listplans, /editplan, /removeplan, /toggleplan,
/sync, /updatesource, /calendar, /logs, /renew
```

---

## Risks و Decisions

### Known Risks (from Architecture)
1. **Single Bot Instance** - Single point of failure
   - Mitigation: Systemd auto-restart، monitoring
   - Post-V1: Distributed execution (Celery)

2. **Polling Payment** - 5 min timeout، possible delays
   - Mitigation: Good logging، user messaging
   - Post-V1: Zarinpal webhook

3. **Rate Limiting** - 0.5s between API calls
   - Mitigation: Async design، efficient queue
   - Post-V1: Optimize with webhook

4. **Trial Reminder Loop** - Every 1 hour check
   - Mitigation: Acceptable latency
   - Post-V1: More frequent if needed

### Architectural Decisions
- ✅ asyncpg instead of ORM → More control
- ✅ Raw SQL instead of QueryBuilder → Clarity
- ✅ One loop vs multiple workers → Simplicity
- ✅ Polling vs webhook (V1) → Implementation simplicity
- ✅ No GraphQL in V1 → Reduce complexity
- ✅ No rate limiting per user in V1 → MVP first

---

## Next Steps (اجرا شروع)

### Step 1: Setup Phase (T01-T05) — 2 روز
- Project structure، database setup، Rubpy client

### Step 2: User Management (T06-T12) — 3 روز
- User registration، trial، subscription prep

### Step 3: Payment (T13-T19) — 3 روز
- Zarinpal integration، transaction handling

### Step 4: Routes & Queues (T20-T28) — 3 روز
- `/addroute`، `/sync`، `/updatesource` commands

### Step 5: Scheduling & Execution (T29-T40) — 4 روز
- All plan types، execution engine، retry logic

### Step 6: Commands & UX (T41-T50) — 3 روز
- All bot commands، Farsi messages، state machine

### Step 7: Admin Dashboard (T51-T62) — 4 روز
- FastAPI routes، HTML pages، integration

### Step 8: Testing & QA (T63-T70) — 3 روز
- Unit، integration، E2E tests، performance

### Step 9: Deploy & Launch (T71-T75) — 2 روز
- Docker، systemd، staging، production

---

## Files Ready for Development

✅ `requirements.txt` - با تمام dependencies  
✅ `.env.example` - configuration template  
✅ `src/config.py` - configuration module  
✅ `src/bot.py` - bot entry point  
✅ `src/database.py` - database utilities  
✅ `Dockerfile` - production build  
✅ `docker-compose.yml` - local development  

---

## Communication & Tracking

### For Claude/AI Agents
- **Reference**: Use task IDs (T01، T02، etc.) from P7
- **Check Status**: docs/P7-WBS-and-milestones.md
- **Update Tracking**: Create EXECUTION_TRACKER.md

### For Human Team
- **Daily Standup**: Check EXECUTION_TRACKER.md
- **Issues**: Create GitHub issues with task ID
- **Questions**: Check docs/ first
- **Decisions**: Update relevant docs immediately

---

## Quality Metrics (V1 Target)

| Metric | Target | Validation |
|--------|--------|------------|
| Unit Test Coverage | 80%+ | pytest |
| API Response Time | < 60s | Logging |
| User Signup Flow | < 3 messages | Manual test |
| Route Creation | < 1 minute | User test |
| Message Forwarding | < 60s delay | Execution logs |
| Uptime | 99%+ | Monitoring |
| Error Rate | < 0.1% | Logs |

---

## Documentation Quality Check

- ✅ All phases P0-P7 documented
- ✅ All tasks with description، owner، duration، deps
- ✅ All risks identified
- ✅ All constraints documented
- ✅ All commands mapped
- ✅ All database tables specified
- ✅ Stack decisions justified
- ✅ User journeys clear
- ✅ V1 scope bounded
- ✅ Post-V1 features deferred

---

## Final Status

```
╔════════════════════════════════════════════════════════════╗
║                  PRE-PRODUCTION COMPLETE                   ║
║                                                             ║
║  Status: ✅ READY FOR EXECUTION                           ║
║  Date:   ۱۴۰۵/۰۲/۲۵ (2026/05/15)                        ║
║  Tasks:  75 identified، ordered، dependency-mapped        ║
║  Docs:   ~4000 lines of specification                      ║
║  Stack:  Chosen، justified، documented                    ║
║                                                             ║
║  Next: Begin M0 (Setup Phase) with T01                    ║
╚════════════════════════════════════════════════════════════╝
```

---

## References

- **PRD**: docs/PRD.md
- **Features**: docs/P2-feature-modules-breakdown.md
- **Architecture**: docs/P3-technical-architecture.md
- **Journeys**: docs/P5-user-journey-and-scope.md
- **Tasks**: docs/P7-WBS-and-milestones.md
- **Roadmap**: docs/pre-production-roadmap.md

---

**Prepared by**: Pre-Production Process  
**Reviewed by**: Architecture & Product Team  
**Approved for Execution**: ✅ YES

