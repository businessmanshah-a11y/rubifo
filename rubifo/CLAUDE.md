# 🧠 دستورالعمل Claude - Rubifo Project

**نسخه**: 2.0  
**تاریخ**: ۱۴۰۵/۰۲/۲۵  
**مخاطب**: Claude AI (All Models)

---

## مقدمه

این دستورالعمل برای Claude است تا دقیقاً درک کند:
1. چه کاری باید انجام دهد
2. چه قوانینی را باید رعایت کند
3. هنگام اتمام چه باید کند
4. چگونه risk و bug را ثبت کند

---

## 1. بخش اول - درک پروژه

### محصول چیست؟

**Rubifo** = ربات فوروارد خودکار برای روبیکا

- کاربران کانال‌های را وصل می‌کنند (مبدأ → مقصد)
- پست‌های خودکار فوروارد می‌شوند
- سه سطح اشتراک + درگاه پرداخت
- داشبورد مدیریتی

### معماری چیست؟

```
┌─ Python 3.10+ (Haiku Coding)
├─ Rubpy (Bot Framework - async)
├─ PostgreSQL (Database)
├─ asyncpg (ORM - raw SQL)
├─ FastAPI (Admin Backend)
└─ Docker + systemd (Deploy)
```

### Database چیست؟

```sql
users, subscriptions, transactions, routes, post_queue, 
schedules, schedule_times, logs
```

**نکته**: از `asyncpg` استفاده می‌شود، نه ORM کامل. SQL خام نوشتن الزامی است.

---

## 2. قبل از شروع Task

### مرحله 1: Task را انتخاب کن

```
1. باز کردن docs/P7-WBS-and-milestones.md
2. یک Task انتخاب کن (مثلاً T01)
3. Check کن dependencies تکمیل‌شده هستند
```

### مرحله 2: وضعیت را آپدیت کن

```markdown
# در EXECUTION_TRACKER.md اپدیت کن:

| T01 | Initialize project structure | Claude | 🔄 In Progress | 2026-05-15 | - |

# در GitHub issue یا comment:
"Starting T01 - Initialize project structure"
```

### مرحله 3: شروع کن

```bash
git checkout -b T##-short-name
# مثلاً: git checkout -b T01-init-project
```

---

## 3. هنگام انجام Task

### ✅ باید انجام دهی:

1. **کد دقیق و تمیز بنویس**
   - Python style: PEP 8
   - Type hints همه جا
   - Docstrings برای functions
   ```python
   async def get_user(user_id: int) -> Optional[User]:
       """Fetch user from database by ID."""
       result = await db.fetchrow("SELECT * FROM users WHERE id = $1", user_id)
       return User(**result) if result else None
   ```

2. **Architecture را رعایت کن**
   - مثلاً: `src/core/user_service.py` برای logic
   - مثلاً: `src/models/user.py` برای models
   - مثلاً: `src/bot/commands.py` برای bot handlers
   - **مثلاً**: NO direct database calls in commands!

3. **Log کن - اگر issue پیدا شد**
   ```markdown
   # در comment یا commit message:
   
   Issue found while implementing T01:
   - asyncpg connection pool initialization failing
   - STATUS: Fixed (need to await init_db())
   ```

4. **اگر Risk دیدی**
   ```markdown
   # در EXECUTION_TRACKER.md اپدیت کن:
   
   ### Risk #1
   - **Task**: T01
   - **Description**: asyncpg pool timeout on large queries
   - **Impact**: High
   - **Mitigation**: Set connection_timeout=30
   - **Status**: Open
   - **Date**: 2026-05-15
   ```

5. **ہر commit برای آپدیت**
   ```bash
   git commit -m "T01: Add project structure and initial files
   
   - Create src/ directory structure
   - Setup logging configuration
   - Create .env.example
   
   Part of T01 milestone setup"
   ```

### ❌ نباید انجام دهی:

1. **خارج از Scope کار نکن**
   - ❌ نوشتن GraphQL (آن post-V1 است)
   - ❌ نوشتن Redis caching (آن post-V1 است)
   - ❌ نوشتن frontend code (آن post-V1 است)
   - ✅ تنها Task description انجام دهد

2. **Architecture را نشکن**
   - ❌ Database query در command handler نویس نکن
   - ❌ Global state اضافه نکن
   - ❌ ORM استفاده نکن (asyncpg only)
   - ✅ Service layer استفاده کن

3. **Dependencies را نادیده نگیر**
   - ❌ T02 را شروع نکن قبل از T01
   - ✅ وابستگی‌ها چک کن اول

4. **Testing را فراموش نکن** (M7 میلستون)
   - ❌ بدون test کد نویسی نکن
   - ✅ Unit tests همراه کد بنویس

---

## 4. بعد از اتمام Task

### مرحله 1: QA خود
```
1. کد خود را بخوان
2. PEP 8 check کن
3. Type hints check کن
4. Docstrings check کن
5. Tests run کن
```

### مرحله 2: Final Commit
```bash
git commit -m "Complete T## - task name

- Feature/fix description
- Part of M# Milestone
- Tests: ✅ passed
- Issues: #X (if any)
- Risks: #X (if any)"

# مثلاً:
git commit -m "Complete T01 - Initialize project structure

- Create src/ directory structure
- Setup logging configuration  
- Create .env.example and Dockerfile
- Add requirements.txt with dependencies

Part of M0 milestone
Tests: ✅ All directory structure tests passed
Issues: None
Risks: None"
```

### مرحله 3: Push
```bash
git push origin T##-short-name
```

### مرحله 4: Update Tracker
```markdown
# در EXECUTION_TRACKER.md اپدیت کن:

| T01 | Initialize... | Claude | ✅ Done | 2026-05-15 | 2026-05-15 | - | - |
```

### مرحله 5: نهایی
```
1. GitHub PR open کن (اگر بخواهند)
2. Add labels: T01, M0
3. Link to docs/P7-WBS-and-milestones.md
```

---

## 5. Code Guidelines

### ✅ DO's

```python
# ✅ Use async/await
async def create_user(user_id: int) -> User:
    await db.execute("INSERT INTO users...")
    return User(id=user_id)

# ✅ Type hints
def calculate_next_run(schedule: Schedule) -> datetime:
    return datetime.now() + timedelta(minutes=schedule.interval)

# ✅ Service layer
class UserService:
    async def get_or_create(self, user_id: int):
        ...

# ✅ Configuration from .env
BOT_TOKEN = os.getenv("BOT_TOKEN")
DB_URL = os.getenv("DATABASE_URL")

# ✅ Parameterized queries
await db.execute("SELECT * FROM users WHERE id = $1", user_id)

# ✅ Error handling
try:
    await forward_message(msg)
except RubikaAPIError as e:
    logger.error(f"Failed to forward: {e}")
    await handle_retry()

# ✅ Logging
logger.info(f"User {user_id} created")
logger.error(f"Database connection failed: {e}")
```

### ❌ DON'Ts

```python
# ❌ Synchronous code
def create_user(user_id):
    db.execute("INSERT...")  # NOT ASYNC!

# ❌ Global state
GLOBAL_USER = None  # NO!

# ❌ Direct DB in command
@bot.on_command("/start")
def handle_start():
    db.execute("INSERT...")  # WRONG! Use service

# ❌ ORM
from sqlalchemy import create_engine  # NO! Use asyncpg

# ❌ String formatting in SQL
query = f"SELECT * FROM users WHERE id = {user_id}"  # SQL INJECTION!

# ❌ Hardcoded values
BOT_TOKEN = "xyz123"  # Use .env!

# ❌ No error handling
await forward_message(msg)  # What if it fails?

# ❌ Print debugging
print("user created")  # Use logger!
```

---

## 6. Architecture Rules

### Folder Structure (نشکن!)

```
src/
├── config.py                    # ✅ Configuration
├── database.py                  # ✅ DB utilities
├── logger.py                    # ✅ Logging
├── bot/
│   ├── main.py                 # ✅ Bot entry
│   ├── commands.py             # ✅ Command handlers
│   └── handlers.py             # ✅ Message handlers
├── core/
│   ├── user_service.py         # ✅ Business logic
│   ├── subscription_service.py
│   ├── route_service.py
│   ├── queue_service.py
│   ├── schedule_service.py
│   ├── calendar_service.py
│   └── execution_engine.py
├── integrations/
│   ├── zarinpal.py             # ✅ Payment gateway
│   └── rubika.py               # ✅ Rubika API
├── admin/
│   ├── main.py                 # ✅ FastAPI app
│   ├── routes.py               # ✅ API endpoints
│   ├── auth.py                 # ✅ Authentication
│   └── static/                 # ✅ HTML/JS/CSS
└── models/
    ├── user.py                 # ✅ Data models
    ├── subscription.py
    ├── route.py
    └── schedule.py
```

### Layer Separation

```
❌ BAD:
@bot.on_message()
def handle():
    db.execute("...")  # Direct DB!

✅ GOOD:
@bot.on_message()
async def handle(msg):
    user_service = UserService(db)
    user = await user_service.get_user(msg.user_id)
    # Service handles DB
```

### Database Access

```
❌ BAD:
result = db.execute("SELECT * FROM users WHERE id = " + str(id))

✅ GOOD:
result = await db.fetchrow("SELECT * FROM users WHERE id = $1", id)
```

---

## 7. Commit Message Format

### Short Task Update
```
T##: Brief description

- Bullet point 1
- Bullet point 2
```

### Completing Task
```
Complete T## - task name

Detailed description of what was done:
- Feature 1
- Feature 2

Part of M# Milestone
Tests: ✅ passed
Issues: None
Risks: None
```

### Bug Fix
```
T##: Fix X issue

Problem: Description
Solution: How it's fixed
Tests: ✅ verified

Closes #X
```

---

## 8. Risk & Issue Logging

### موارد Risk:

```markdown
### Risk #1 (T37)
- **Description**: Single bot instance failure
- **Impact**: High (bot goes down, no messages sent)
- **Probability**: Medium (servers can crash)
- **Mitigation**: 
  - Auto-restart via systemd RestartAlways
  - Monitoring + alerts
  - Graceful shutdown + recovery
- **Status**: Open → Mitigated
```

### موارد Bug:

```markdown
### Issue #1 (T25)
- **Task**: T25 - Implement /updatesource
- **Description**: New posts not added to queue
- **Steps to Reproduce**:
  1. Create route
  2. Add new post to source channel
  3. Run /updatesource
- **Expected**: New post in queue
- **Actual**: Not appearing
- **Root Cause**: Missing ORDER BY source_date
- **Fix**: Add ORDER BY to query
- **Status**: RESOLVED (commit abc123)
```

---

## 9. Testing Expectations

### Minimal Testing per Task

```python
# T01: Test project structure
assert os.path.exists("src/")
assert os.path.exists("src/config.py")

# T07: Test /start command
async def test_start_command():
    user = await user_service.get_or_create(123)
    assert user.trial_active == True

# T37: Test execution loop
async def test_execution_loop():
    # Create schedule with post_queue
    # Run execution_engine
    # Assert post marked as 'sent'
```

---

## 10. Documentation Requirements

### Per Task:
- ✅ Code comments برای complex logic
- ✅ Docstrings برای functions
- ✅ Update relevant docs/ files
- ✅ Update EXECUTION_TRACKER.md

### Example:
```python
async def calculate_next_run(schedule: Schedule) -> datetime:
    """
    Calculate next execution time for a schedule.
    
    Handles two methods:
    - interval: Add interval_minutes to current time
    - daily_count: Fetch from schedule_times table
    
    Args:
        schedule: Schedule object with type and parameters
    
    Returns:
        Next execution datetime
    
    Raises:
        ValueError: If schedule_type invalid
    """
    if schedule.schedule_type == "interval":
        # Calculate based on interval
        ...
    else:
        # Calculate based on daily distribution
        ...
```

---

## 11. When in Doubt

### سوالات متداول:

**Q: باید ORM استفاده کنم؟**  
A: نه! صرفاً asyncpg استفاده کن.

**Q: چگونه dependency رو مدیریت کنم؟**  
A: Dependency injection pass کن. Global state نه.

**Q: اگر Task dependencies ندارد انجام شود؟**  
A: نه! EXECUTION_TRACKER check کن.

**Q: چند بار commit کنم؟**  
A: هر کار منطقی = 1 commit. در انتهای Task = 1 final commit.

**Q: اگر risk پیدا شد چی کنم؟**  
A: ثبتش کن در EXECUTION_TRACKER.md و commit.

**Q: اگر ساختار کو غیر موافقت؟**  
A: نه! Docs confirm کن اول.

---

## 12. Checklist برای اتمام Task

```
Before starting:
☐ Task ID selected (T##)
☐ Dependencies checked
☐ EXECUTION_TRACKER updated (In Progress)
☐ Branch created (T##-short-name)

During development:
☐ Code follows PEP 8
☐ Type hints everywhere
☐ Docstrings added
☐ Architecture rules followed
☐ Tests written (if applicable)
☐ No hardcoded values
☐ Logging added
☐ Error handling complete

Before finishing:
☐ Self-review done
☐ All tests pass
☐ Branch pushed
☐ Final commit message good
☐ EXECUTION_TRACKER updated (Done)
☐ Issues/Risks logged (if any)
☐ Documentation updated

After finishing:
☐ Next task dependency checked
☐ Team notified
☐ GitHub ready for review
```

---

## 13. نقاط انجمنی

### هنگام کار با کدکس:
- از `src/` حذف نکن (که درست هست)
- Files فارسی (دستورالعمل) درست parsing می‌شود

### هنگام کار با Git:
- commits شفاف و توضیحی باشند
- Branch names clear باشند (T##-short-name)

### هنگام مشکل در API:
- Rubika API docs check کن
- اگر rate limited، 0.5s delay add کن

---

## خلاصه

| مرحله | عمل |
|------|------|
| 📝 شروع | Select task، Update tracker، Create branch |
| 💻 انجام | Code ← Architecture، Test ← Code، Log ← Issues |
| ✅ اتمام | Self-review، Final commit، Push، Update tracker |
| 📊 بعد | Check next dependencies |

---

**برای سوالات**: Check docs/ و P7-WBS-and-milestones.md

**اخرین به‌روزرسانی**: ۱۴۰۵/۰۲/۲۵

