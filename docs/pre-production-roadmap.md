# نقشه راه پیش‌تولید Rubifo
**تاریخ:** ۱۴۰۵/۰۲/۲۵ | ۲۰۲۶/۰۵/۱۵  
**وضعیت:** در حال آماده‌سازی برای اجرا  
**مبنا:** دستورالعمل جامع پیش‌تولید

---

## مراحل پیش‌تولید

| فاز | عنوان | وضعیت | خروجی |
|-----|-------|--------|--------|
| P0 | آماده‌سازی SSOT | ✅ تمام | docs/ و PRD |
| P1 | تعریف بیزینس و محصول | ✅ تمام | PRD.md |
| P2 | تفکیک فیچرها و ماژول‌ها | ⏳ در انتظار | Feature Master Plan |
| P3 | معماری فنی | ⏳ در انتظار | Technical Architecture |
| P4 | سیستم طراحی و UI | ⏳ در انتظار | Design System |
| P5 | نقشه سایت و User Journey | ⏳ در انتظار | Site Map |
| P6 | تصمیم‌های Scope و MVP | ⏳ در انتظار | MVP Boundaries |
| P7 | WBS و برنامه فازبندی | ⏳ در انتظار | Tasks و Milestones |
| P8 | سیستم اجرای AI | ⏳ در انتظار | CLAUDE.md، AGENTS.md |
| P9 | چک‌لیست‌های اجرا | ⏳ در انتظار | Deploy/Content Checklists |

---

## مرحله بعدی: P2 - تفکیک فیچرها و ماژول‌ها

### هدف
شکستن محصول (Rubifo Bot) به ماژول‌های مستقل و قابل توسعه

### ماژول‌های پیش‌فرض (از PRD):
1. **User Management** - ثبت‌نام، تریال، اشتراک
2. **Subscription & Payment** - سطوح اشتراک، درگاه پرداخت، مدیریت renewal
3. **Route Management** - تعریف مسیرها، مدیریت چنل‌های مبدأ و مقصد
4. **Post Queue System** - صف پست‌ها، وضعیت، خطاها
5. **Schedule System** - زمانبندی، interval و daily count methods
6. **Execution Engine** - حلقه اجرا، عملیات فوروارد، retry logic
7. **Content Calendar** - تقویم محتوایی مقصد
8. **Admin Dashboard** - داشبورد مدیریتی
9. **Bot Commands** - دستورات روبات (/start، /addroute، etc.)
10. **Logging & Error Handling** - لاگ‌ها و خطاها

### خروجی
```
docs/_تفکیک فیچرها و ماژول‌های سیستم.md
```

---

## نکات مهم پیش‌تولید Rubifo

- **No Production Coding**: تا زمانی که تمام اسناد روشن نشوند، کد نمی‌نویسیم
- **Docs are SSOT**: تمام تصمیم‌ها باید در سندها ثبت شوند
- **V1 vs Post-V1**: باید مشخص شود چی در V1 است و چی برای بعدها
- **Architecture First**: معماری قبل از کد
- **Dependencies Clear**: وابستگی‌های ماژول‌ها مشخص باشند

---

## جدول زمانی تخمینی

- P2: ۲ روز
- P3: ۳ روز
- P4: ۲ روز (اگر UI ساده باشد)
- P5: ۲ روز
- P6: ۱ روز
- P7: ۲ روز
- P8: ۱ روز
- P9: ۱ روز

**جمع: ~۱۴ روز pre-production**

