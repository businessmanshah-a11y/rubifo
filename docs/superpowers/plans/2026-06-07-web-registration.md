# Web Registration & Bot Linking — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** کاربران بتوانند از طریق سایت ثبت‌نام کنند و بعداً حساب خود را به ربات روبیکا لینک کنند بدون اینکه داده‌هایشان از دست برود.

**Architecture:** کاربر سایتی یک `user_id = "web_<token>"` موقت می‌گیرد. وقتی ربات را باز می‌کند، ربات یک bot-user جدید با Rubika GUID می‌سازد. در مرحله ورود شماره تلفن، ربات تشخیص می‌دهد که این شماره متعلق به یک حساب سایتی است — رمز عبور را تأیید می‌کند — سپس در یک تراکنش اتمیک همه FKها (subscriptions, transactions, logs) به rubika_guid منتقل می‌شوند و رکورد web حذف می‌شود. JWT کاربر پس از merge باطل می‌شود و کاربر یک‌بار مجدداً لاگین می‌کند.

**Tech Stack:** Python 3.10+, asyncpg, FastAPI, bcrypt, PostgreSQL, Rubpy bot

**Design Spec:** `docs/superpowers/specs/2026-06-07-web-registration-design.md`

---

## File Map

| فایل | نوع تغییر | توضیح |
|------|-----------|-------|
| `migrations/013_add_rubika_user_id.sql` | جدید | ADD COLUMN rubika_user_id |
| `src/models/user.py` | ویرایش | اضافه کردن فیلد rubika_user_id |
| `src/core/user_service.py` | ویرایش | متدهای create_web_user، merge_web_account |
| `app.py` | ویرایش | endpoint ثبت‌نام + آپدیت صفحه login |
| `src/bot/commands.py` | ویرایش | linking flow + handler جدید |

---

## Task 1: Migration 013 — اضافه کردن ستون rubika_user_id

**Files:**
- Create: `migrations/013_add_rubika_user_id.sql`

- [ ] **Step 1: بنویس فایل migration**

```sql
-- Migration 013: Add rubika_user_id column for web-first user linking
-- web users: rubika_user_id IS NULL (not yet linked to bot)
-- bot users (existing): rubika_user_id = user_id (same Rubika GUID)
-- after linking: rubika_user_id = user_id = rubika_guid

ALTER TABLE users ADD COLUMN IF NOT EXISTS rubika_user_id TEXT UNIQUE;

-- Backfill existing bot users (user_id = Rubika GUID, not web_ prefix)
UPDATE users SET rubika_user_id = user_id WHERE user_id NOT LIKE 'web_%';

CREATE INDEX IF NOT EXISTS idx_users_rubika_user_id ON users(rubika_user_id)
  WHERE rubika_user_id IS NOT NULL;
```

- [ ] **Step 2: اجرا کن migration**

```bash
python migrations/run_migrations.py
```

Expected: migration 013 اجرا شود بدون خطا

- [ ] **Step 3: تأیید در DB**

```bash
psql $DATABASE_URL -c "\d users" | grep rubika_user_id
```

Expected: ستون `rubika_user_id text` نمایش داده شود

- [ ] **Step 4: commit**

```bash
git add migrations/013_add_rubika_user_id.sql
git commit -m "T: Add rubika_user_id column for web-first user account linking"
```

---

## Task 2: آپدیت User Model

**Files:**
- Modify: `src/models/user.py`

- [ ] **Step 1: اضافه کردن فیلد rubika_user_id**

فایل `src/models/user.py` را ویرایش کن — فیلد `rubika_user_id` را بعد از `user_id` اضافه کن:

```python
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class User:
    """User model representing a Rubifo user."""

    id: int = 0
    user_id: str = ""
    rubika_user_id: Optional[str] = None
    username: Optional[str] = None
    trial_start_at: datetime = datetime.now()
    trial_end_at: Optional[datetime] = None
    is_trial_active: bool = True
    phone_number: Optional[str] = None
    password_hash: Optional[str] = None
    onboarding_completed_at: Optional[datetime] = None
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()
```

- [ ] **Step 2: تأیید — import کن و خطا نگیر**

```bash
cd /Users/infinite/Desktop/rubifo
python3 -c "from src.models.user import User; u = User(); print(u.rubika_user_id)"
```

Expected: `None`

- [ ] **Step 3: commit**

```bash
git add src/models/user.py
git commit -m "T: Add rubika_user_id field to User model"
```

---

## Task 3: متدهای جدید UserService

**Files:**
- Modify: `src/core/user_service.py`

دو متد جدید اضافه می‌شود:
1. `create_web_user` — ثبت‌نام از طریق سایت
2. `merge_web_account` — ادغام حساب سایتی به ربات

- [ ] **Step 1: اضافه کردن `create_web_user` به user_service.py**

بعد از متد `authenticate_web_user` اضافه کن:

```python
async def create_web_user(self, phone_number: str, password: str) -> User:
    """Create a new user from web registration (no Rubika bot link yet).

    user_id is a stable synthetic key prefixed 'web_'.
    Trial does NOT start here — it starts when the bot is linked.
    """
    import secrets
    normalized = self.normalize_phone(phone_number)
    hashed = self.hash_password(password)
    web_id = "web_" + secrets.token_hex(12)

    await self.db.execute(
        """
        INSERT INTO users (user_id, phone_number, password_hash, is_trial_active)
        VALUES ($1, $2, $3, FALSE)
        """,
        web_id,
        normalized,
        hashed,
    )
    user = await self.get_user(web_id)
    logger.info(f"Web user created: {web_id} phone={normalized}")
    return user

async def merge_web_account(
    self, web_user_id: str, rubika_guid: str
) -> User:
    """Merge a web-registered user into an existing bot user.

    Transfers all FK data (subscriptions, transactions, logs) from the
    web placeholder user to the rubika_guid user, then deletes the placeholder.
    Trial starts on the rubika_guid user upon merge.
    JWT tokens for web_user_id become invalid after this call.
    """
    web_user = await self.get_user(web_user_id)
    if not web_user:
        raise ValueError(f"Web user {web_user_id} not found")

    async with self.db.acquire() as conn:
        async with conn.transaction():
            for table in ("subscriptions", "transactions", "logs"):
                await conn.execute(
                    f"UPDATE {table} SET user_id = $1 WHERE user_id = $2",
                    rubika_guid,
                    web_user_id,
                )
            await conn.execute(
                "DELETE FROM users WHERE user_id = $1", web_user_id
            )
            result = await conn.fetchrow(
                """
                UPDATE users SET
                    phone_number         = $1,
                    password_hash        = $2,
                    rubika_user_id       = $3,
                    onboarding_completed_at = NOW(),
                    is_trial_active      = TRUE,
                    trial_start_at       = NOW(),
                    trial_end_at         = NOW() + INTERVAL '72 hours',
                    updated_at           = NOW()
                WHERE user_id = $3
                RETURNING *
                """,
                web_user.phone_number,
                web_user.password_hash,
                rubika_guid,
            )

    merged = User(**dict(result))
    logger.info(f"Merged web account {web_user_id} → bot user {rubika_guid}")
    return merged
```

**نکته درباره `self.db.acquire()`:** asyncpg pool از این pattern پشتیبانی می‌کند. اطمینان حاصل کن که `self.db` همان pool است.

- [ ] **Step 2: تست import**

```bash
python3 -c "from src.core.user_service import UserService; print('OK')"
```

Expected: `OK`

- [ ] **Step 3: commit**

```bash
git add src/core/user_service.py
git commit -m "T: Add create_web_user and merge_web_account to UserService"
```

---

## Task 4: Endpoint ثبت‌نام + آپدیت صفحه Login

**Files:**
- Modify: `app.py`

### بخش 4-A: Pydantic model و endpoint ثبت‌نام

- [ ] **Step 1: اضافه کردن `_UserRegisterBody`**

بعد از `_UserLoginBody` در `app.py` اضافه کن:

```python
class _UserRegisterBody(BaseModel):
    phone_number: str
    password: str
    confirm_password: str
```

- [ ] **Step 2: اضافه کردن endpoint ثبت‌نام**

بعد از `@app.post("/api/auth/login")` endpoint اضافه کن:

```python
@app.post("/api/auth/register")
async def web_user_register(body: _UserRegisterBody):
    if body.password != body.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="رمز عبور و تکرار آن یکسان نیستند.",
        )
    svc = UserService(_web_db())
    try:
        phone = UserService.normalize_phone(body.phone_number)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="فرمت شماره موبایل صحیح نیست. مثال: 09123456789",
        )
    existing = await svc.get_user_by_phone(phone)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="این شماره قبلاً ثبت‌نام کرده. از تب ورود وارد شوید.",
        )
    try:
        UserService.hash_password(body.password)  # validates length >= 6
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="رمز عبور باید حداقل ۶ کاراکتر باشد.",
        )
    user = await svc.create_web_user(body.phone_number, body.password)
    return {
        "access_token": _create_user_token(user.user_id),
        "token_type": "bearer",
        "user": {
            "user_id": user.user_id,
            "phone_number": user.phone_number,
        },
    }
```

- [ ] **Step 3: تست endpoint با curl**

```bash
curl -s -X POST http://127.0.0.1:8765/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"phone_number":"09100000001","password":"test123","confirm_password":"test123"}' \
  | python3 -m json.tool
```

Expected: `{ "access_token": "eyJ...", "token_type": "bearer", "user": {...} }`

- [ ] **Step 4: تست خطای تکراری**

```bash
curl -s -X POST http://127.0.0.1:8765/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"phone_number":"09100000001","password":"test123","confirm_password":"test123"}' \
  | python3 -m json.tool
```

Expected: HTTP 409 با پیام «این شماره قبلاً ثبت‌نام کرده»

### بخش 4-B: آپدیت صفحه `/login` با تب‌ها

- [ ] **Step 5: جایگزینی `web_login_page` با نسخه دو-تبه**

تابع `web_login_page` را در `app.py` کامل جایگزین کن:

```python
@app.get("/login")
async def web_login_page(next: str = "/checkout", tier: str = ""):
    safe_next = _safe_next_path(next)
    action_hint = f"{safe_next}?tier={tier}" if tier else safe_next
    tier_name = _tier_label(tier) if tier else "پلن انتخابی"
    return _html_page(
        "ورود / ثبت‌نام — Rubifo",
        f"""
        <div class="checkout-copy">
          <div class="brand-mark">Rubifo</div>
          <h1>حساب روبیفو</h1>
          <p class="lead">برای خرید {escape(tier_name)} وارد شوید یا حساب جدید بسازید.</p>
        </div>
        <div class="checkout-panel">
          <!-- Tabs -->
          <div class="tab-bar" style="display:flex;background:rgba(255,255,255,0.04);
               border-radius:10px;padding:4px;margin-bottom:24px;
               border:1px solid rgba(255,255,255,0.06);">
            <button id="tab-login" onclick="switchTab('login')"
              style="flex:1;padding:9px;border-radius:7px;border:none;cursor:pointer;
                     font-size:13px;font-weight:600;background:#a855f7;color:white;
                     transition:all 0.2s;">ورود</button>
            <button id="tab-register" onclick="switchTab('register')"
              style="flex:1;padding:9px;border-radius:7px;border:none;cursor:pointer;
                     font-size:13px;font-weight:600;background:transparent;color:#888;
                     transition:all 0.2s;">ثبت‌نام</button>
          </div>

          <!-- Login Form -->
          <div id="panel-login">
            <div class="panel-kicker">ورود کاربر</div>
            <h2 class="panel-title">خوش برگشتی</h2>
            <form id="login-form">
              <div class="field">
                <label>شماره تماس</label>
                <input name="phone_number" autocomplete="tel" inputmode="tel"
                       placeholder="09123456789" required>
              </div>
              <div class="field">
                <label>رمز عبور</label>
                <input name="password" type="password" autocomplete="current-password" required>
              </div>
              <button class="btn btn-primary" type="submit">ورود به حساب</button>
            </form>
            <p id="login-error" class="error-note"></p>
            <div class="button-row">
              <a class="btn btn-ghost" href="{RUBIKA_BOT_RETURN_URL}">ثبت‌نام در ربات</a>
            </div>
          </div>

          <!-- Register Form -->
          <div id="panel-register" style="display:none">
            <div class="panel-kicker">ثبت‌نام</div>
            <h2 class="panel-title">ساخت حساب رایگان</h2>
            <form id="register-form">
              <div class="field">
                <label>شماره موبایل</label>
                <input name="phone_number" autocomplete="tel" inputmode="tel"
                       placeholder="09123456789" required>
              </div>
              <div class="field">
                <label>رمز عبور (حداقل ۶ کاراکتر)</label>
                <input name="password" type="password" autocomplete="new-password" required>
              </div>
              <div class="field">
                <label>تکرار رمز عبور</label>
                <input name="confirm_password" type="password" autocomplete="new-password" required>
              </div>
              <button class="btn btn-primary" type="submit">ساخت حساب و شروع</button>
            </form>
            <p id="register-error" class="error-note"></p>
          </div>
        </div>

        <script>
        function switchTab(tab) {{
          const isLogin = tab === 'login';
          document.getElementById('panel-login').style.display = isLogin ? '' : 'none';
          document.getElementById('panel-register').style.display = isLogin ? 'none' : '';
          document.getElementById('tab-login').style.background = isLogin ? '#a855f7' : 'transparent';
          document.getElementById('tab-login').style.color = isLogin ? 'white' : '#888';
          document.getElementById('tab-register').style.background = isLogin ? 'transparent' : '#a855f7';
          document.getElementById('tab-register').style.color = isLogin ? '#888' : 'white';
        }}

        document.getElementById('login-form').addEventListener('submit', async (e) => {{
          e.preventDefault();
          const form = new FormData(e.currentTarget);
          const res = await fetch('/api/auth/login', {{
            method: 'POST',
            headers: {{'Content-Type': 'application/json'}},
            body: JSON.stringify({{
              phone_number: form.get('phone_number'),
              password: form.get('password')
            }})
          }});
          if (!res.ok) {{
            let msg = 'ورود انجام نشد.';
            try {{ msg = (await res.json()).detail || msg; }} catch {{}}
            document.getElementById('login-error').textContent = msg;
            return;
          }}
          const data = await res.json();
          localStorage.setItem('rubifo_user_token', data.access_token);
          window.location.href = {action_hint!r};
        }});

        document.getElementById('register-form').addEventListener('submit', async (e) => {{
          e.preventDefault();
          const form = new FormData(e.currentTarget);
          const res = await fetch('/api/auth/register', {{
            method: 'POST',
            headers: {{'Content-Type': 'application/json'}},
            body: JSON.stringify({{
              phone_number: form.get('phone_number'),
              password: form.get('password'),
              confirm_password: form.get('confirm_password')
            }})
          }});
          if (!res.ok) {{
            let msg = 'خطا در ثبت‌نام.';
            try {{ msg = (await res.json()).detail || msg; }} catch {{}}
            document.getElementById('register-error').textContent = msg;
            return;
          }}
          const data = await res.json();
          localStorage.setItem('rubifo_user_token', data.access_token);
          window.location.href = '/plans';
        }});
        </script>
        """,
        page_class="login-page",
    )
```

- [ ] **Step 6: تست صفحه login**

مرورگر را باز کن و `http://127.0.0.1:8765/login` را بررسی کن:
- تب «ورود» پیش‌فرض فعال باشد
- کلیک روی «ثبت‌نام» فرم سوم فیلد را نشان دهد
- فرم ثبت‌نام با شماره جدید کار کند

- [ ] **Step 7: commit**

```bash
git add app.py
git commit -m "T: Add /api/auth/register endpoint and tabbed login/register page"
```

---

## Task 5: Bot Linking Flow — آپدیت commands.py

**Files:**
- Modify: `src/bot/commands.py`

### بخش 5-A: آپدیت `handle_web_onboarding_phone`

- [ ] **Step 1: جایگزینی `handle_web_onboarding_phone`**

تابع موجود `handle_web_onboarding_phone` را کامل جایگزین کن:

```python
async def handle_web_onboarding_phone(client, user_id: str, text: str) -> None:
    """Collect phone number. Detects web-registered accounts and routes to linking."""
    from src.database import pool
    from src.core.user_service import UserService

    try:
        phone_number = UserService.normalize_phone(text)
    except ValueError:
        conversation_states[user_id] = {"command": "web_onboarding_phone"}
        await client.send_message(
            user_id,
            "❌ شماره تماس معتبر نیست.\n"
            "لطفاً شماره موبایل را با فرمت 09xxxxxxxxx وارد کنید."
        )
        return

    svc = UserService(pool)
    existing = await svc.get_user_by_phone(phone_number)

    if existing and existing.rubika_user_id is None:
        # Web-registered user — must verify password before linking
        conversation_states[user_id] = {
            "command": "web_linking_password_verify",
            "web_user_id": existing.user_id,
            "attempts": 0,
        }
        await client.send_message(
            user_id,
            "🔗 این شماره یک حساب سایتی دارد.\n\n"
            "برای اتصال ربات به حسابت، رمز عبور سایت را وارد کن:"
        )
        return

    if existing and existing.rubika_user_id is not None:
        # Phone already linked to another bot account
        conversation_states[user_id] = {"command": "web_onboarding_phone"}
        await client.send_message(
            user_id,
            "❌ این شماره به حساب دیگری متصل است.\n"
            "لطفاً شماره دیگری وارد کنید."
        )
        return

    # Normal flow — new user, ask for password
    conversation_states[user_id] = {
        "command": "web_onboarding_password",
        "phone_number": phone_number,
    }
    await client.send_message(
        user_id,
        "✅ شماره تماس ثبت شد.\n\n"
        "حالا یک رمز عبور برای ورود به وب‌سایت انتخاب کنید.\n"
        "رمز باید حداقل ۶ کاراکتر باشد."
    )
```

### بخش 5-B: اضافه کردن `handle_web_linking_password_verify`

- [ ] **Step 2: اضافه کردن handler جدید** (بعد از `handle_web_onboarding_phone`)

```python
async def handle_web_linking_password_verify(
    client, user_id: str, text: str
) -> None:
    """Verify web account password before linking bot to it."""
    from src.database import pool
    from src.core.user_service import UserService

    state = conversation_states.get(user_id, {})
    web_user_id = state.get("web_user_id")
    attempts = state.get("attempts", 0)

    if not web_user_id:
        conversation_states[user_id] = {"command": "web_onboarding_phone"}
        await client.send_message(user_id, "خطا. لطفاً دوباره شماره را وارد کنید.")
        return

    svc = UserService(pool)
    web_user = await svc.get_user(web_user_id)

    if not web_user or not web_user.password_hash:
        conversation_states.pop(user_id, None)
        await client.send_message(user_id, "خطایی رخ داد. لطفاً دوباره /start بفرستید.")
        return

    password = (text or "").strip()
    if not UserService.verify_password(password, web_user.password_hash):
        attempts += 1
        if attempts >= 3:
            conversation_states.pop(user_id, None)
            await client.send_message(
                user_id,
                "❌ سه بار اشتباه وارد کردید. لطفاً دوباره /start بفرستید."
            )
            return
        conversation_states[user_id] = {
            "command": "web_linking_password_verify",
            "web_user_id": web_user_id,
            "attempts": attempts,
        }
        remaining = 3 - attempts
        await client.send_message(
            user_id,
            f"❌ رمز اشتباه است. {remaining} بار دیگر فرصت دارید."
        )
        return

    # Password correct — merge accounts
    try:
        merged_user = await svc.merge_web_account(web_user_id, str(user_id))
        conversation_states.pop(user_id, None)
        await client.send_message(
            user_id,
            f"✅ حسابت با شماره {merged_user.phone_number} به ربات وصل شد!\n\n"
            "تریال ۷۲ ساعته‌ات از همین الان شروع شد. 🎉\n\n"
            "⚠️ اگر قبلاً در سایت وارد بودی، لطفاً یک‌بار دیگر لاگین کن.",
            with_keypad=True,
        )
        await _send_start_home(client, str(user_id), merged_user)
    except Exception as e:
        logger.error(f"merge_web_account failed for {user_id}: {e}")
        conversation_states.pop(user_id, None)
        await client.send_message(user_id, "خطا در اتصال حساب. لطفاً دوباره /start بفرستید.")
```

### بخش 5-C: آپدیت dispatch در `handle_conversation_response`

- [ ] **Step 3: اضافه کردن case جدید به `handle_conversation_response`**

در تابع `handle_conversation_response` (که switch-case روی `command` دارد) این case را اضافه کن:

```python
elif command == "web_linking_password_verify":
    await handle_web_linking_password_verify(client, user_id, text)
```

این خط را بعد از `elif command == "web_onboarding_password":` اضافه کن.

- [ ] **Step 4: تست import**

```bash
python3 -c "from src.bot.commands import handle_web_linking_password_verify; print('OK')"
```

Expected: `OK`

- [ ] **Step 5: commit**

```bash
git add src/bot/commands.py
git commit -m "T: Add web account linking flow to bot — phone detection, password verify, merge"
```

---

## Task 6: تست End-to-End

- [ ] **Step 1: سرور را راه‌اندازی کن**

```bash
/Users/infinite/Library/Python/3.9/bin/uvicorn app:app --host 127.0.0.1 --port 8765
```

- [ ] **Step 2: تست ثبت‌نام سایت**

```bash
curl -s -X POST http://127.0.0.1:8765/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"phone_number":"09199999999","password":"webpass1","confirm_password":"webpass1"}' \
  | python3 -m json.tool
```

Expected: JWT صادر شود، `user_id` با `web_` شروع شود

- [ ] **Step 3: تأیید در DB**

```bash
psql $DATABASE_URL -c "SELECT user_id, rubika_user_id, is_trial_active FROM users WHERE phone_number='09199999999';"
```

Expected:
```
user_id       | rubika_user_id | is_trial_active
web_abc123... | NULL           | f
```

- [ ] **Step 4: تست ورود با همین شماره**

```bash
curl -s -X POST http://127.0.0.1:8765/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"phone_number":"09199999999","password":"webpass1"}' \
  | python3 -m json.tool
```

Expected: JWT صادر شود

- [ ] **Step 5: تست لینک ربات (شبیه‌سازی دستی)**

```bash
# شبیه‌سازی merge_web_account با Python
python3 << 'EOF'
import asyncio, asyncpg, os

async def test():
    pool = await asyncpg.create_pool(os.environ['DATABASE_URL'])
    from src.core.user_service import UserService
    svc = UserService(pool)
    
    # ساختن bot user شبیه /start
    bot_user = await svc.get_or_create_user("TESTBOTGUID001", "testbot")
    print(f"Bot user created: {bot_user.user_id}")
    
    # merge
    web_user = await svc.get_user_by_phone("09199999999")
    if web_user and web_user.rubika_user_id is None:
        merged = await svc.merge_web_account(web_user.user_id, "TESTBOTGUID001")
        print(f"Merged: user_id={merged.user_id} trial={merged.is_trial_active}")
    
    await pool.close()

asyncio.run(test())
EOF
```

Expected:
```
Bot user created: TESTBOTGUID001
Merged: user_id=TESTBOTGUID001 trial=True
```

- [ ] **Step 6: تأیید در DB پس از merge**

```bash
psql $DATABASE_URL -c "SELECT user_id, rubika_user_id, is_trial_active, phone_number FROM users WHERE phone_number='09199999999';"
```

Expected:
```
user_id        | rubika_user_id | is_trial_active | phone_number
TESTBOTGUID001 | TESTBOTGUID001 | t               | 09199999999
```

(رکورد `web_abc123...` دیگر وجود ندارد)

- [ ] **Step 7: تأیید JWT قدیمی باطل شد**

```bash
# از access_token مرحله 2 استفاده کن
curl -s http://127.0.0.1:8765/api/me/subscription \
  -H "Authorization: Bearer <OLD_WEB_JWT>" | python3 -m json.tool
```

Expected: HTTP 401 — «User not found»

- [ ] **Step 8: لاگین مجدد و تأیید JWT جدید**

```bash
curl -s -X POST http://127.0.0.1:8765/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"phone_number":"09199999999","password":"webpass1"}' \
  | python3 -m json.tool
```

Expected: JWT جدید با `user_id = TESTBOTGUID001`

- [ ] **Step 9: پاک‌سازی داده‌های تست**

```bash
psql $DATABASE_URL -c "DELETE FROM users WHERE user_id='TESTBOTGUID001';"
```

- [ ] **Step 10: commit نهایی**

```bash
git add -A
git commit -m "T: Web registration and bot linking implementation complete"
```

---

## خلاصه تغییرات

| | فایل | تغییر |
|--|------|-------|
| ✅ | `migrations/013_add_rubika_user_id.sql` | ADD COLUMN + backfill |
| ✅ | `src/models/user.py` | فیلد rubika_user_id |
| ✅ | `src/core/user_service.py` | create_web_user + merge_web_account |
| ✅ | `app.py` | endpoint ثبت‌نام + صفحه login با تب |
| ✅ | `src/bot/commands.py` | linking flow + handler جدید |

**کاربران قدیمی ربات:** هیچ تغییری نمی‌کنند — migration فقط یک ستون اضافه می‌کند.
