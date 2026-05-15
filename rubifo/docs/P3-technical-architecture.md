# P3 - معماری فنی و دستورالعمل توسعه
**تاریخ:** ۱۴۰۵/۰۲/۲۵ | ۲۰۲۶/۰۵/۱۵  
**وضعیت:** ✅ تمام

---

## خلاصه تصمیم‌های معماری

| جزء | انتخاب | دلیل |
|-----|--------|------|
| **زبان اصلی** | Python 3.10+ | async-first، کمپایلری نیست، سریع‌تر توسعه |
| **Bot Framework** | Rubpy (async) | کارایی بالا، پشتیبانی webhook/poll، async native |
| **Database** | PostgreSQL | JSONB، row-level lock، transactions قوی |
| **ORM/Query** | Asyncpg (raw SQL) | کم‌تر complexity، کنترل کامل، بهتر برای async |
| **Scheduling** | Python asyncio loop | simple، بدون وابستگی خارجی، async-native |
| **Payment Gateway** | Zarinpal | پرداخت ایرانی، API سادگی، polling+webhook |
| **Admin Backend** | FastAPI | async، OpenAPI docs، minimal overhead |
| **Admin Frontend** | HTML/CSS/JS + Alpine.js | سبک، بدون build step، یا AdminLTE |
| **DevOps** | Docker + systemd | containerization، easy deployment |
| **Monitoring** | Rotating logs + Sentry (post-V1) | basic logs now، Sentry later |

---

## ۱. معماری کلی (High-Level)

```
┌─────────────────────────────────────────────────────────────┐
│                    Rubika Platform                          │
│  (Source Channels ↔ Bot ↔ Target Channels)                 │
└────────────────────────┬────────────────────────────────────┘
                         │
                ┌────────▼────────┐
                │  Rubpy Client   │ (Async connection to Rubika)
                └────────┬────────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
    ┌────▼────┐    ┌────▼────┐    ┌───▼─────┐
    │ Bot Core│    │ Admin   │    │ Payment │
    │ Executor│    │ FastAPI │    │ Gateway │
    └────┬────┘    └────┬────┘    └───┬─────┘
         │              │             │
         └──────────────┼─────────────┘
                        │
                ┌───────▼────────┐
                │  PostgreSQL    │
                │  (Main DB)     │
                └────────────────┘
```

---

## ۲. ساختار Folder و File

```
rubifo/
├── src/
│   ├── __init__.py
│   ├── config.py                 # تنظیمات و environment
│   ├── database.py               # اتصال PostgreSQL
│   ├── logger.py                 # تنظیمات logging
│   │
│   ├── bot/
│   │   ├── __init__.py
│   │   ├── main.py              # Bot entry point
│   │   ├── handlers.py          # Message handlers
│   │   ├── commands.py          # /start، /addroute، etc.
│   │   └── client.py            # Rubpy Client wrapper
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── user_service.py      # User Management
│   │   ├── subscription_service.py # Subscription & Payment
│   │   ├── route_service.py     # Route Management
│   │   ├── queue_service.py     # Post Queue System
│   │   ├── schedule_service.py  # Schedule System
│   │   ├── calendar_service.py  # Content Calendar
│   │   └── execution_engine.py  # Main executor loop
│   │
│   ├── integrations/
│   │   ├── __init__.py
│   │   ├── zarinpal.py          # Payment gateway
│   │   └── rubika.py            # Rubika API wrapper
│   │
│   ├── admin/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI app
│   │   ├── auth.py              # Authentication
│   │   ├── routes.py            # API endpoints
│   │   ├── schemas.py           # Pydantic models
│   │   └── static/              # HTML/CSS/JS templates
│   │
│   └── models/
│       ├── __init__.py
│       ├── user.py
│       ├── subscription.py
│       ├── route.py
│       ├── post_queue.py
│       ├── schedule.py
│       └── transaction.py
│
├── migrations/
│   ├── 001_init_schema.sql
│   └── 002_indexes.sql
│
├── tests/
│   ├── __init__.py
│   ├── test_user_service.py
│   ├── test_queue_service.py
│   └── conftest.py              # pytest fixtures
│
├── docs/
│   ├── PRD.md
│   ├── P2-feature-modules-breakdown.md
│   ├── P3-technical-architecture.md
│   ├── DB_SCHEMA.md
│   └── ... (other docs)
│
├── .env.example
├── .env                         # (git ignored)
├── requirements.txt
├── docker-compose.yml
├── Dockerfile
├── docker-entrypoint.sh
├── CLAUDE.md                    # تعلیمات Claude
├── AGENTS.md                    # تعلیمات agents
├── README.md
└── .gitignore
```

---

## ۳. Database Schema (خطوط کلی)

### users
```sql
id SERIAL PRIMARY KEY
user_id BIGINT UNIQUE                    -- Rubika user ID
username VARCHAR(255)
trial_start_at TIMESTAMP
trial_end_at TIMESTAMP
is_trial_active BOOLEAN DEFAULT true
created_at TIMESTAMP DEFAULT NOW()
updated_at TIMESTAMP DEFAULT NOW()
```

### subscriptions
```sql
id SERIAL PRIMARY KEY
user_id BIGINT REFERENCES users(id)
tier VARCHAR(50)                        -- basic, pro, enterprise
start_date DATE
end_date DATE
is_active BOOLEAN DEFAULT true
created_at TIMESTAMP DEFAULT NOW()
```

### transactions
```sql
id SERIAL PRIMARY KEY
user_id BIGINT REFERENCES users(id)
amount INTEGER                          -- Rials
tier VARCHAR(50)
status VARCHAR(50)                      -- pending, completed, failed
reference_id VARCHAR(255)               -- Zarinpal ref
created_at TIMESTAMP DEFAULT NOW()
```

### routes
```sql
id SERIAL PRIMARY KEY
user_id BIGINT REFERENCES users(id)
source_channel_id BIGINT               -- Rubika channel ID
target_channel_id BIGINT               -- Rubika channel ID
is_active BOOLEAN DEFAULT true
created_at TIMESTAMP DEFAULT NOW()
```

### post_queue
```sql
id SERIAL PRIMARY KEY
route_id BIGINT REFERENCES routes(id)
message_id_in_source BIGINT            -- Rubika message ID
source_date TIMESTAMP                   -- When msg was sent in source
status VARCHAR(50)                      -- pending, sent, failed, removed
retry_count INTEGER DEFAULT 0
last_error TEXT
created_at TIMESTAMP DEFAULT NOW()
```

### schedules
```sql
id SERIAL PRIMARY KEY
route_id BIGINT REFERENCES routes(id)
schedule_type VARCHAR(50)              -- interval, daily_count
time_spec JSONB                        -- {start_time, end_time, interval_minutes, ...}
posts_per_run INTEGER DEFAULT 1
loop_mode BOOLEAN DEFAULT false
next_run TIMESTAMP
is_active BOOLEAN DEFAULT true
last_run TIMESTAMP
created_at TIMESTAMP DEFAULT NOW()
```

### schedule_times (فقط برای daily_count)
```sql
id SERIAL PRIMARY KEY
schedule_id BIGINT REFERENCES schedules(id)
scheduled_time TIMESTAMP
status VARCHAR(50) DEFAULT 'pending'   -- pending, done
```

### logs
```sql
id SERIAL PRIMARY KEY
schedule_id BIGINT REFERENCES schedules(id)
post_queue_id BIGINT REFERENCES post_queue(id)
status VARCHAR(50)                      -- success, retry, failed
error_message TEXT
created_at TIMESTAMP DEFAULT NOW()
```

---

## ۴. Flow اجرای رئیسی

### A. شروع ربات

```python
# src/bot/main.py

async def main():
    await init_db()                      # اتصال PostgreSQL
    await init_admin_server()            # FastAPI server
    
    client = await init_rubika_client()  # Rubpy client
    
    # ثبت handlers
    @client.on_message_receive()
    async def handle_message(user_id, message):
        # Parse command و call handlers
        
    # شروع execution loop
    asyncio.create_task(execution_engine_loop())
    
    # شروع trial reminder loop
    asyncio.create_task(trial_reminder_loop())
    
    # شروع Rubika client
    await client.run()

async def execution_engine_loop():
    while True:
        await execute_pending_schedules()
        await asyncio.sleep(30)

async def trial_reminder_loop():
    while True:
        await check_trial_reminders()
        await asyncio.sleep(3600)        # هر ساعت
```

### B. تصمیم کاربر برای `/addroute`

```
1. کاربر /addroute می‌فرستد
2. ربات: "شناسه کانال مبدأ را بفرست"
3. کاربر: "@mychannel"
4. ربات: بررسی خود admin است یا نه
5. اگر بله: "شناسه کانال مقصد را بفرست"
6. اگر خیر: "خطا، ربات در آن کانال admin نیست"
7. کاربر: "@targetchannel"
8. ربات: دوباره بررسی
9. اگر بله: خواندن تمام پست‌های موجود و پر کردن صف
10. ایجاد route و route_id را به کاربر بدن
```

### C. Execution Engine Loop

```python
async def execute_pending_schedules():
    schedules = await db.fetch("""
        SELECT * FROM schedules 
        WHERE is_active = true AND next_run <= NOW()
    """)
    
    for schedule in schedules:
        try:
            async with db.transaction():
                # Lock row
                post = await db.fetchrow("""
                    SELECT * FROM post_queue
                    WHERE route_id = $1 AND status = 'pending'
                    ORDER BY source_date ASC
                    LIMIT 1
                    FOR UPDATE
                """, schedule.route_id)
                
                if not post:
                    if schedule.loop_mode:
                        # Reset queue
                        await reset_queue_for_loop(schedule.route_id)
                    else:
                        # Deactivate
                        await deactivate_schedule(schedule.id)
                    continue
                
                # Try to forward
                try:
                    await forward_message(post, schedule.target_channel_id)
                    await mark_as_sent(post.id)
                except Exception as e:
                    await handle_forward_error(post, e)
                
                # Calculate next_run
                next_run = calculate_next_run(schedule)
                await update_schedule_next_run(schedule.id, next_run)
        
        except Exception as e:
            await log_error(schedule.id, e)
```

---

## ۵. Async Patterns

### Concurrency Model
- **Single Event Loop**: یک asyncio loop برای تمام operationها
- **Connection Pool**: asyncpg pool (۱۰-۲۰ connections)
- **Queue Safety**: SELECT FOR UPDATE برای row locking

### Rate Limiting
```python
RUBIKA_API_DELAY = 0.5  # seconds between API calls

async def forward_message(post, target_channel_id):
    await asyncio.sleep(RUBIKA_API_DELAY)
    await client.send_message(target_channel_id, post.content)
```

---

## ۶. Error Handling Strategy

### Levels
1. **Try-Catch at Command Level**: `/addroute` - user-facing errors
2. **Try-Catch at Service Level**: queue operations - log و retry
3. **Try-Catch at Engine Loop**: catch all، log without breaking loop

### Retry Logic
```python
if post.retry_count < 3:
    post.retry_count += 1
    post.last_error = error_message
    schedule.next_run = NOW() + 5minutes  # Try again
    await log_error(schedule.id, post.id, 'retry')
else:
    post.status = 'failed'
    await log_error(schedule.id, post.id, 'final_failure')
```

### Critical Errors
- Bot not admin in channel → deactivate schedule، message to user
- Channel doesn't exist → deactivate schedule، message to user
- Network failure → retry (backoff optional in post-V1)

---

## ۷. Admin API (FastAPI)

### Structure
```python
# src/admin/main.py

app = FastAPI()

@app.post("/admin/login")
async def login(username, password):
    # Verify JWT or session
    
@app.get("/admin/dashboard/stats")
@require_auth
async def get_stats():
    # Return user/plan/message counts
    
@app.get("/admin/users")
@require_auth
async def list_users(page, limit):
    # Paginated user list
    
@app.post("/admin/users/{user_id}/message")
@require_auth
async def send_message_to_user(user_id, text):
    # Send message through bot
    
@app.get("/admin/logs")
@require_auth
async def get_logs(user_id, plan_id, from_date, to_date):
    # Fetch logs with filters
```

### Authentication
- JWT + session cookie
- Username/password hash bcrypt
- .env: `ADMIN_USERNAME`، `ADMIN_PASSWORD_HASH`

---

## ۸. DevOps & Deployment

### Local Development
```bash
# Docker Compose
docker-compose up -d postgres  # PostgreSQL
python -m src.bot.main         # Bot
python -m src.admin.main       # Admin API
```

### Systemd Service (Production)
```ini
[Unit]
Description=Rubifo Bot
After=network.target postgresql.service

[Service]
Type=simple
User=rubifo
WorkingDirectory=/opt/rubifo
ExecStart=/opt/rubifo/venv/bin/python -m src.bot.main
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Docker
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "-m", "src.bot.main"]
```

---

## ۹. نقاط مهم طراحی

### ۱. No Global State
- Database connections via pool
- Rubya client passed to functions
- Logging injected

### ۲. Testability
- Services layer (no direct DB calls in commands)
- Dependency injection for Rubya client
- Mock-friendly architecture

### ۳. Observability
- Structured logging with timestamp, level, context
- Log to file with rotation
- Error tracking (Sentry in post-V1)

### ۴. Safety
- Input validation (Pydantic)
- SQL injection prevention (parameterized queries)
- Rate limiting per user (post-V1)

---

## ۱۰. V1 vs Post-V1

### V1 شامل
- Python + Rubpy + PostgreSQL
- Asyncpg (raw SQL)
- FastAPI admin
- Zarinpal (polling)
- Rotating logs
- Basic Docker

### Post-V1 (بعدی)
- GraphQL API
- Redis caching
- Webhook from Zarinpal
- Distributed execution (Celery/RQ)
- Advanced monitoring (Sentry)
- Multiple payment gateways
- i18n beyond Farsi
- User API (for mobile app)

---

## نتیجه‌گیری P3

✅ معماری انتخاب شده است  
✅ Folder structure مشخص است  
✅ Database schema خطوط کلی است  
✅ Async patterns شفاف است  
✅ Admin API طراحی شده است  
✅ V1 vs Post-V1 جدا است  

**مراحل بعدی:**  
- P4: سیستم طراحی (اگر UI خاصی لازم است)
- P5: نقشه سایت و User Journey
- P6: MVP Boundaries و scope finalization

