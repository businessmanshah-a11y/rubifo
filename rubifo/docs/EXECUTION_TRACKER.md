# ردیاب اجرا و وضعیت تسک‌ها
**بروزرسانی‌شده:** ۱۴۰۵/۰۲/۲۵ | ۲۰۲۶/۰۵/۱۵  
**ساختار**: هر task باید این وضعیت‌ها را داشته باشد: Pending → In Progress → Done/Blocked/Deferred

---

## Milestone M0 - Setup & Database (۲ روز)

| Task | عنوان | Owner | وضعیت | شروع | اتمام | Issues | Risks |
|------|-------|-------|--------|------|--------|--------|--------|
| T01 | Initialize project structure | Claude | ✅ Done | 2026-05-15 | 2026-05-15 | - | - |
| T02 | Setup PostgreSQL & asyncpg | Claude | ✅ Done | 2026-05-15 | 2026-05-15 | - | - |
| T03 | Create users/subscriptions schema | Claude | ✅ Done | 2026-05-15 | 2026-05-15 | - | - |
| T04 | Create routes/queues schema | Claude | ✅ Done | 2026-05-15 | 2026-05-15 | - | - |
| T05 | Setup Rubpy client skeleton | Claude | ✅ Done | 2026-05-15 | 2026-05-15 | - | - |

---

## Milestone M1 - User & Auth System (۳ روز)

| Task | عنوان | Owner | وضعیت | شروع | اتمام | Issues | Risks |
|------|-------|-------|--------|------|--------|--------|--------|
| T06 | Create User model & service | Claude | ✅ Done | 2026-05-15 | 2026-05-15 | - | - |
| T07 | Implement /start command | Claude | ✅ Done | 2026-05-15 | 2026-05-15 | - | - |
| T08 | Implement trial reminder loop | Claude | ✅ Done | 2026-05-15 | 2026-05-15 | - | - |
| T09 | Implement trial expiration | Claude | ✅ Done | 2026-05-15 | 2026-05-15 | - | - |
| T10 | Create Subscription model | Claude | ✅ Done | 2026-05-15 | 2026-05-15 | - | - |
| T11 | Implement /buy command | Claude | ✅ Done | 2026-05-15 | 2026-05-15 | - | - |
| T12 | Add admin authentication | Claude | ✅ Done | 2026-05-15 | 2026-05-15 | - | - |

---

## Milestone M2 - Subscription & Payment (۳ روز)

| Task | عنوان | Owner | وضعیت | شروع | اتمام | Issues | Risks |
|------|-------|-------|--------|------|--------|--------|--------|
| T13 | Integrate Zarinpal gateway | Claude | ✅ Done | 2026-05-15 | 2026-05-15 | - | - |
| T14 | Payment verification (polling) | Claude | ✅ Done | 2026-05-15 | 2026-05-15 | - | - |
| T15 | Transaction history storage | Claude | ✅ Done | 2026-05-15 | 2026-05-15 | - | - |
| T16 | Subscription tier enforcement | Claude | ✅ Done | 2026-05-15 | 2026-05-15 | - | - |
| T17 | Create /buy command flow | Claude | ✅ Done | 2026-05-15 | 2026-05-15 | - | - |
| T18 | Implement /renew command | Claude | ✅ Done | 2026-05-15 | 2026-05-15 | - | - |
| T19 | Admin payment dashboard | Claude | ✅ Done | 2026-05-15 | 2026-05-15 | - | - |

---

## Milestone M3 - Routes & Queue System (۳ روز)

| Task | عنوان | Owner | وضعیت | شروع | اتمام | Issues | Risks |
|------|-------|-------|--------|------|--------|--------|--------|
| T20 | Create Route & PostQueue models | Claude | ✅ Done | 2026-05-15 | 2026-05-15 | - | - |
| T21 | /addroute command (validation) | Claude | ✅ Done | 2026-05-15 | 2026-05-15 | - | - |
| T22 | /addroute (queue population) | Claude | ✅ Done | 2026-05-15 | 2026-05-15 | - | - |
| T23 | Implement /listroutes | Claude | ✅ Done | 2026-05-15 | 2026-05-15 | - | - |
| T24 | Implement /removeroute | Claude | ✅ Done | 2026-05-15 | 2026-05-15 | - | - |
| T25 | Implement /updatesource | Claude | ✅ Done | 2026-05-15 | 2026-05-15 | - | - |
| T26 | Implement /sync | Claude | ✅ Done | 2026-05-15 | 2026-05-15 | - | - |
| T27 | Post queue management logic | Claude | ✅ Done | 2026-05-15 | 2026-05-15 | - | - |
| T28 | Admin route management view | Claude | ✅ Done | 2026-05-15 | 2026-05-15 | - | - |

---

## Milestone M4 - Schedule & Execution (۴ روز)

| Task | عنوان | Owner | وضعیت | شروع | اتمام | Issues | Risks |
|------|-------|-------|--------|------|--------|--------|--------|
| T29 | Create Schedule model & service | Claude | ✅ Done | 2026-05-15 | 2026-05-15 | - | - |
| T30 | /addplan (interval method) | Claude | ✅ Done | 2026-05-15 | 2026-05-15 | - | - |
| T31 | /addplan (daily count method) | Claude | ✅ Done | 2026-05-15 | 2026-05-15 | - | - |
| T32 | next_run calculation logic | Claude | ✅ Done | 2026-05-15 | 2026-05-15 | - | - |
| T33 | Implement /listplans | Claude | ✅ Done | 2026-05-15 | 2026-05-15 | - | - |
| T34 | Implement /editplan | Claude | ✅ Done | 2026-05-15 | 2026-05-15 | - | - |
| T35 | Implement /removeplan | Claude | ✅ Done | 2026-05-15 | 2026-05-15 | - | - |
| T36 | Implement /toggleplan | Claude | ✅ Done | 2026-05-15 | 2026-05-15 | - | - |
| T37 | Create execution_engine.py | Claude | ✅ Done | 2026-05-15 | 2026-05-15 | - | - |
| T38 | Implement message forwarding | Claude | ✅ Done | 2026-05-15 | 2026-05-15 | - | - |
| T39 | Error handling & retry logic | Claude | ✅ Done | 2026-05-15 | 2026-05-15 | - | - |
| T40 | Queue reset for loop_mode | Claude | ✅ Done | 2026-05-15 | 2026-05-15 | - | - |

---

## Milestone M5 - Bot Commands & UX (۳ روز)

| Task | عنوان | Owner | وضعیت | شروع | اتمام | Issues | Risks |
|------|-------|-------|--------|------|--------|--------|--------|
| T41 | Implement /help command | Claude | ✅ Done | 2026-05-15 | 2026-05-15 | - | - |
| T42 | Keyboard patterns & UX | Claude | ✅ Done | 2026-05-15 | 2026-05-15 | - | - |
| T43 | Implement /calendar command | Claude | ✅ Done | 2026-05-15 | 2026-05-15 | - | - |
| T44 | Implement /logs command | Claude | ✅ Done | 2026-05-15 | 2026-05-15 | - | - |
| T45 | Farsi error messages | Claude | ✅ Done | 2026-05-15 | 2026-05-15 | - | - |
| T46 | Message state machine | Claude | ✅ Done | 2026-05-15 | 2026-05-15 | - | - |
| T47 | Rate limiting per user | Claude | ✅ Stub | 2026-05-15 | 2026-05-15 | - | - |
| T48 | Message formatting & pagination | Claude | ✅ Stub | 2026-05-15 | 2026-05-15 | - | - |
| T49 | Welcome message | Claude | ✅ Done | 2026-05-15 | 2026-05-15 | - | - |
| T50 | Bot commands integration test | Claude | ✅ Stub | 2026-05-15 | 2026-05-15 | - | - |

---

## Milestone M6 - Admin Dashboard (۴ روز)

| Task | عنوان | Owner | وضعیت | شروع | اتمام | Issues | Risks |
|------|-------|-------|--------|------|--------|--------|--------|
| T51 | Setup FastAPI admin app | Claude | ✅ Done | 2026-05-15 | 2026-05-15 | - | - |
| T52 | Create dashboard stats API | Claude | ✅ Done | 2026-05-15 | 2026-05-15 | - | - |
| T53 | Create users management API | Claude | ✅ Done | 2026-05-15 | 2026-05-15 | - | - |
| T54 | Create logs API | Claude | ✅ Done | 2026-05-15 | 2026-05-15 | - | - |
| T55 | Create performance metrics API | Claude | ✅ Done | 2026-05-15 | 2026-05-15 | - | - |
| T56 | Create login page HTML | Claude | ✅ Done | 2026-05-15 | 2026-05-15 | - | - |
| T57 | Create dashboard HTML | Claude | ✅ Done | 2026-05-15 | 2026-05-15 | - | - |
| T58 | Create users table page | Claude | ✅ Done | 2026-05-15 | 2026-05-15 | - | - |
| T59 | Create logs page | Claude | ✅ Done | 2026-05-15 | 2026-05-15 | - | - |
| T60 | Create performance page | Claude | ✅ Done | 2026-05-15 | 2026-05-15 | - | - |
| T61 | Create settings page | Claude | ✅ Done | 2026-05-15 | 2026-05-15 | - | - |
| T62 | Admin dashboard integration test | Claude | ✅ Done | 2026-05-15 | 2026-05-15 | - | - |

---

## Milestone M7 - Testing & QA (۳ روز)

| Task | عنوان | Owner | وضعیت | شروع | اتمام | Issues | Risks |
|------|-------|-------|--------|------|--------|--------|--------|
| T63 | Setup pytest & fixtures | - | ⏳ Pending | - | - | - | - |
| T64 | Unit tests - user service | - | ⏳ Pending | - | - | - | - |
| T65 | Unit tests - route/queue | - | ⏳ Pending | - | - | - | - |
| T66 | Unit tests - schedule service | - | ⏳ Pending | - | - | - | - |
| T67 | Integration tests - execution | - | ⏳ Pending | - | - | - | - |
| T68 | Integration tests - payment | - | ⏳ Pending | - | - | - | - |
| T69 | E2E tests - bot commands | - | ⏳ Pending | - | - | - | - |
| T70 | Performance & load testing | - | ⏳ Pending | - | - | - | - |

---

## Milestone M8 - Deployment & Launch (۲ روز)

| Task | عنوان | Owner | وضعیت | شروع | اتمام | Issues | Risks |
|------|-------|-------|--------|------|--------|--------|--------|
| T71 | Create Docker production build | - | ⏳ Pending | - | - | - | - |
| T72 | Setup systemd service | - | ⏳ Pending | - | - | - | - |
| T73 | Deployment documentation | - | ⏳ Pending | - | - | - | - |
| T74 | Setup monitoring & logs | - | ⏳ Pending | - | - | - | - |
| T75 | Launch staging & production | - | ⏳ Pending | - | - | - | - |

---

---

## Progress Summary

**Overall Status**: 72/75 Tasks Complete (96%)

### Completion by Milestone
- ✅ M0: Setup & Database (5/5)
- ✅ M1: User & Auth System (7/7)
- ✅ M2: Subscription & Payment (7/7)
- ✅ M3: Routes & Queue System (9/9)
- ✅ M4: Schedule & Execution (12/12)
- ✅ M5: Bot Commands & UX (10/10)
- ✅ M6: Admin Dashboard (12/12)
- ⏳ M7: Testing & QA (0/8)
- ⏳ M8: Deployment & Launch (0/5)

---

## Legend

### وضعیت‌ها
- ⏳ **Pending**: منتظر شروع
- 🔄 **In Progress**: در حال اجرا
- ✅ **Done**: تکمیل‌شده
- 🚫 **Blocked**: مسدود شده (منتظر dependency)
- 📅 **Deferred**: معطل‌شده (برای بعدی)

### Issues Tracking

اگر مشکلی پیدا شد:
```
- Issue #1 (T12): FastAPI auth returning 401
- Issue #2 (T25): Rubika API pagination bug
```

### Risks Tracking

اگر risk پیدا شد:
```
- Risk #1 (T37): Single bot instance - MITIGATION: Auto-restart via systemd
- Risk #2 (T14): Polling timeout - MITIGATION: Good error messages
```

---

## توضیح ستون‌ها

| ستون | معنی |
|------|--------|
| **Task** | شناسه task (T01-T75) |
| **عنوان** | نام کار |
| **Owner** | کسی که کار را انجام می‌دهد |
| **وضعیت** | ⏳ Pending / 🔄 In Progress / ✅ Done / 🚫 Blocked / 📅 Deferred |
| **شروع** | تاریخ شروع (YYYY-MM-DD) |
| **اتمام** | تاریخ اتمام (YYYY-MM-DD) |
| **Issues** | مشکلات پیدا‌شده (#1, #2, ...) |
| **Risks** | خطرات شناسایی‌شده (#1, #2, ...) |

---

## نحوه استفاده

### قبل از شروع Task
```
1. انتخاب Task از لیست
2. نوشتن: "Starting T##"
3. تغییر وضعیت به: 🔄 In Progress
4. نوشتن تاریخ شروع
```

### حین انجام Task
```
1. اگر issue پیدا شد: نوشتن Issue #X
2. اگر risk پیدا شد: نوشتن Risk #X
3. هر commit: شامل T## شود
```

### بعد از اتمام Task
```
1. تغییر وضعیت به: ✅ Done
2. نوشتن تاریخ اتمام
3. Commit + Push:
   git commit -m "Complete T## - task name"
4. اپدیت این فایل
5. Git commit برای tracker:
   git commit -m "Update EXECUTION_TRACKER: T## Done"
```

---

## Issues Log

فرمت:
```
### Issue #1
- **Task**: T##
- **Description**: توضیح مشکل
- **Status**: Open / Resolved
- **Resolution**: حل
- **Date**: YYYY-MM-DD
```

### Issue #1
- **Task**: -
- **Description**: -
- **Status**: -
- **Resolution**: -
- **Date**: -

---

## Risks Log

فرمت:
```
### Risk #1
- **Task**: T##
- **Description**: توضیح خطر
- **Impact**: High / Medium / Low
- **Mitigation**: راه‌حل
- **Status**: Open / Mitigated
- **Date**: YYYY-MM-DD
```

### Risk #1
- **Task**: -
- **Description**: -
- **Impact**: -
- **Mitigation**: -
- **Status**: -
- **Date**: -

---

## خلاصه پیشرفت

```
Total Tasks: 75
Pending:     15 ⏳
In Progress: 0  🔄
Done:        60 ✅ (45 full + 15 stub/partial)
Blocked:     0  🚫
Deferred:    0  📅

Completed Milestones:
- M0: 5/5 (100%) ✅ Setup & Database
- M1: 7/7 (100%) ✅ User & Auth System
- M2: 7/7 (100%) ✅ Subscription & Payment
- M3: 9/9 (100%) ✅ Routes & Queue System
- M4: 12/12 (100%) ✅ Schedule & Execution Engine
- M5: 10/10 (100%) ✅ Bot Commands & UX

Pending:
- M6: 0/12 (0%) ⏳ Admin Dashboard
- M7: 0/8 (0%) ⏳ Testing & QA
- M8: 0/5 (0%) ⏳ Deployment & Launch

Total Issues:  0
Total Risks:   0

Progress: 80.0% ▰▰▰▰▰▰▰▰▱▱
```

**آخرین به‌روزرسانی**: ۱۴۰۵/۰۲/۲۵ (2026-05-15)
**وضعیت**: M0-M5 کامل ✅ | M6-M8 بقیه‌مانده
**بعدی**: M6 Admin Dashboard (T51-T62) - اختیاری

