# Outbound IP Monitor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a 10-minute outbound IP monitor that records the Rubifo PaaS egress IP, alerts Telegram only when it changes, and shows status in the admin panel.

**Architecture:** A focused async service in `src/core/outbound_ip_monitor.py` owns IP fetching, state persistence, comparison, and Telegram alerting. FastAPI startup ensures the database table exists and starts a background loop when monitoring is enabled. Admin routes expose the latest state and a manual check endpoint; `settings.html` renders the status.

**Tech Stack:** FastAPI, asyncpg, httpx, pytest, pytest-asyncio, ParsPack environment variables, Telegram Bot API.

---

### Task 1: Configuration and State Schema

**Files:**
- Modify: `src/config.py`
- Create: `migrations/014_outbound_ip_monitor.sql`
- Modify: `app.py`

- [ ] **Step 1: Write failing tests for monitor config defaults**

Create tests in `tests/test_outbound_ip_monitor.py` asserting the monitor service can be instantiated without Telegram credentials and reports alerting as disabled.

- [ ] **Step 2: Add config values**

Add:

```python
OUTBOUND_IP_CHECK_ENABLED = os.getenv("OUTBOUND_IP_CHECK_ENABLED", "true").lower() not in {"0", "false", "no"}
OUTBOUND_IP_CHECK_INTERVAL_SECONDS = int(os.getenv("OUTBOUND_IP_CHECK_INTERVAL_SECONDS", "600"))
OUTBOUND_IP_CHECK_URL = os.getenv("OUTBOUND_IP_CHECK_URL", "https://api.ipify.org")
TELEGRAM_ALERT_BOT_TOKEN = os.getenv("TELEGRAM_ALERT_BOT_TOKEN", "")
TELEGRAM_ALERT_CHAT_ID = os.getenv("TELEGRAM_ALERT_CHAT_ID", "")
```

- [ ] **Step 3: Add migration and startup table ensure**

Create `outbound_ip_monitor` with one row keyed by `id = 1`, current/previous IP, status, timestamps, and last error. In startup, call the service table ensure so existing deployments do not depend on a manual migration before boot.

### Task 2: Monitor Service

**Files:**
- Create: `src/core/outbound_ip_monitor.py`
- Test: `tests/test_outbound_ip_monitor.py`

- [ ] **Step 1: Write failing tests for first check, unchanged IP, changed IP, and fetch failure**

Tests use fake DB and fake HTTP functions. Assertions:
- First successful check stores `current_ip` and sends no Telegram alert.
- Same IP later sends no alert.
- Changed IP stores `previous_ip`, sets `status = changed`, and sends one alert.
- Fetch error stores `status = error` and no alert.

- [ ] **Step 2: Implement service**

Implement `OutboundIPMonitor` with:
- `ensure_table()`
- `get_status()`
- `check_once()`
- `run_forever()`
- Telegram alert through `httpx.AsyncClient.post`.

### Task 3: Admin API and UI

**Files:**
- Modify: `src/admin/routes.py`
- Modify: `src/admin/static/settings.html`
- Test: `tests/test_admin_dashboard.py`

- [ ] **Step 1: Write API tests**

Assert `/admin/outbound-ip-status` requires auth and returns monitor fields. Assert `/admin/outbound-ip-check` requires auth and returns check result.

- [ ] **Step 2: Add admin routes**

Add:
- `GET /admin/outbound-ip-status`
- `POST /admin/outbound-ip-check`

- [ ] **Step 3: Add settings UI card**

Add a "مانیتور IP خروجی" setting item showing current IP, previous IP, last check, status, and a manual check button.

### Task 4: Deployment Assets and Verification

**Files:**
- Modify: `.env` locally only, not committed
- Update: `docs/rubifo-deploy.zip`

- [ ] **Step 1: Add local env values**

Set:

```dotenv
TELEGRAM_ALERT_BOT_TOKEN=<provided token>
TELEGRAM_ALERT_CHAT_ID=<telegram chat id>
OUTBOUND_IP_CHECK_INTERVAL_SECONDS=600
OUTBOUND_IP_CHECK_ENABLED=true
```

- [ ] **Step 2: Run tests**

Run:

```bash
pytest tests/test_outbound_ip_monitor.py tests/test_admin_dashboard.py -q
```

- [ ] **Step 3: Update deploy zip**

Regenerate `docs/rubifo-deploy.zip` from deployable project files while excluding `.env`, `.git`, caches, logs, and old archives.

- [ ] **Step 4: Final verification, commit, and push**

Run focused tests again, inspect `git diff`, commit source changes and zip, verify `.env` is not staged, then push to `origin`.
