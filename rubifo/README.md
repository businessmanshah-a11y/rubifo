# Rubifo - ربات فوروارد هوشمند روبیکا

ربات خودکار فوروارد برای پلتفرم روبیکا با پشتیبانی از زمانبندی پیشرفته و مدیریت اشتراک.

## خصوصیات

- 🤖 **فوروارد خودکار**: پست‌های کانال مبدأ را به کانال مقصد فوروارد کنید
- 📅 **زمانبندی پیشرفته**: دو روش زمانبندی (interval و daily count)
- 💳 **سیستم اشتراک**: سه سطح اشتراک با درگاه پرداخت زرین‌پال
- 📊 **تقویم محتوایی**: مشاهده برنامه ارسال پست‌ها
- 🎛️ **داشبورد مدیریتی**: آمار کامل سیستم و مدیریت کاربران
- 🇮🇷 **فارسی**: رابط کاربری کامل به فارسی

## وضعیت پروژه

✅ **Pre-Production Complete** - آماده برای اجرا

- ✅ P0: SSOT آماده‌شده
- ✅ P1: PRD تکمیل‌شده
- ✅ P2: ماژول‌ها شناسایی‌شده
- ✅ P3: معماری انتخاب‌شده
- ✅ P5: User Journey تعریف‌شده
- ✅ P6: MVP Boundaries مشخص
- ✅ P7: 75 Task برنامه‌ریزی‌شده
- ⏳ P8: دستورالعمل‌های AI
- ⏳ P9: چک‌لیست‌های Deployment

[مشاهده وضعیت کامل](docs/PRE-PRODUCTION-STATUS.md)

## معماری فنی

```
Python 3.10+ | Rubpy | PostgreSQL | FastAPI | asyncio
```

- **Bot Framework**: Rubpy (async)
- **Database**: PostgreSQL با asyncpg
- **Admin Backend**: FastAPI
- **Admin Frontend**: HTML/CSS/JavaScript
- **DevOps**: Docker + systemd

[مشاهده معماری کامل](docs/P3-technical-architecture.md)

## شروع کار

### پیش‌نیازها

- Python 3.10+
- PostgreSQL 12+
- Docker (optional)

### نصب توسعه‌ای

```bash
# Clone repository
git clone https://github.com/businessmanshah-a11y/rubifo.git
cd rubifo

# Setup virtual environment
python -m venv venv
source venv/bin/activate  # یا venv\Scripts\activate روی Windows

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Edit .env with your settings

# Start PostgreSQL (Docker)
docker-compose up -d postgres

# Run migrations
python -m src.database

# Run bot
python -m src.bot.main

# Run admin dashboard (in another terminal)
python -m src.admin.main
```

## دستورات ربات

| دستور | توضیح |
|-------|--------|
| `/start` | ثبت‌نام و شروع تریال |
| `/help` | راهنمای کامل |
| `/buy` | خرید اشتراک |
| `/addroute` | ایجاد مسیر جدید |
| `/listroutes` | نمایش مسیرها |
| `/addplan` | ایجاد پلان زمانبندی |
| `/calendar` | تقویم محتوایی |
| `/logs` | نمایش لاگ خطاها |

[تمام دستورات](docs/P5-user-journey-and-scope.md)

## Documentation

- 📘 [Product Requirements (PRD)](docs/PRD.md)
- 📦 [Module Breakdown](docs/P2-feature-modules-breakdown.md)
- 🏗️ [Technical Architecture](docs/P3-technical-architecture.md)
- 🎯 [User Journeys & Scope](docs/P5-user-journey-and-scope.md)
- 📋 [WBS & Milestones](docs/P7-WBS-and-milestones.md)
- 📊 [Pre-Production Status](docs/PRE-PRODUCTION-STATUS.md)
- 🛣️ [Development Roadmap](docs/pre-production-roadmap.md)

## Development Tasks

75 tasks identified in [WBS](docs/P7-WBS-and-milestones.md):

- **M0**: Setup (5 tasks)
- **M1**: User Management (7 tasks)
- **M2**: Subscription & Payment (7 tasks)
- **M3**: Routes & Queues (9 tasks)
- **M4**: Scheduling & Execution (12 tasks)
- **M5**: Bot Commands & UX (10 tasks)
- **M6**: Admin Dashboard (12 tasks)
- **M7**: Testing & QA (8 tasks)
- **M8**: Deployment & Launch (5 tasks)

## Contributing

1. Select task from [WBS](docs/P7-WBS-and-milestones.md)
2. Create branch: `git checkout -b T##-task-name`
3. Follow [architecture guidelines](docs/P3-technical-architecture.md)
4. Update task status in EXECUTION_TRACKER.md
5. Create pull request

## Support

For questions or issues:
1. Check [documentation](docs/)
2. Check [FAQs](docs/PRD.md#سوالات-متداول) (if exists)
3. Create GitHub issue with context

## License

Proprietary - Rubifo Project

## Contact

📧 businessmanshah@outlook.com

---

**Last Updated**: ۱۴۰۵/۰۲/۲۵ (2026/05/15)  
**Status**: ✅ Pre-Production Complete

