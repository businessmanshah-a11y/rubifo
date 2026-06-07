# Header Auth Dropdown Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a profile icon button to the landing page header that opens a smart dropdown for login/register/subscription status, with no new routes or DB migrations.

**Architecture:** Two files change only. `app.py` gets three small backend tweaks (phone claim in JWT, tab param on `/login`, allow `/#plans` in safe-next). `src/admin/static/index.html` gets CSS, an HTML button+dropdown element, and a JS auth module wired to localStorage + `/api/me/subscription`.

**Tech Stack:** Python/FastAPI (app.py), Vanilla JS + inline CSS (index.html), `python-jose` for JWT, existing `/api/me/subscription` endpoint.

---

## Files Changed

| File | Change |
|------|--------|
| `app.py` | Add `phone` claim to JWT, `tab` param to `/login`, fix `_safe_next_path` |
| `src/admin/static/index.html` | Auth button HTML, dropdown CSS, client auth JS |

---

## Task 1: Add `phone` claim to JWT in `app.py`

**Files:**
- Modify: `app.py:104-113` (`_create_user_token`)
- Modify: `app.py:608-609` (`web_user_login` caller)
- Modify: `app.py:648-649` (`web_user_register` caller)

- [ ] **Step 1: Update `_create_user_token` signature and payload**

Replace the function at line 104:

```python
def _create_user_token(user_id: str, phone_number: str = "") -> str:
    from datetime import datetime, timedelta

    payload = {
        "scope": "web_user",
        "sub": user_id,
        "phone": phone_number,
        "exp": datetime.utcnow() + timedelta(hours=_USER_TOKEN_EXP_HOURS),
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, USER_JWT_SECRET, algorithm=_USER_TOKEN_ALG)
```

- [ ] **Step 2: Update `web_user_login` caller (line ~609)**

Change:
```python
"access_token": _create_user_token(user.user_id),
```
To:
```python
"access_token": _create_user_token(user.user_id, user.phone_number or ""),
```

- [ ] **Step 3: Update `web_user_register` caller (line ~649)**

Change:
```python
"access_token": _create_user_token(user.user_id),
```
To:
```python
"access_token": _create_user_token(user.user_id, user.phone_number or ""),
```

- [ ] **Step 4: Verify no other callers of `_create_user_token`**

```bash
grep -n "_create_user_token" /Users/infinite/Desktop/rubifo/app.py
```
Expected: only lines 104, ~609, ~649.

- [ ] **Step 5: Commit**

```bash
git add app.py
git commit -m "T: Add phone claim to web user JWT token"
```

---

## Task 2: Add `tab` query param to `/login` page in `app.py`

**Files:**
- Modify: `app.py:459-591` (`web_login_page`)

- [ ] **Step 1: Add `tab` param to the route handler signature**

Change line 460:
```python
async def web_login_page(next: str = "/checkout", tier: str = ""):
```
To:
```python
async def web_login_page(next: str = "/checkout", tier: str = "", tab: str = "login"):
```

- [ ] **Step 2: Inject `switchTab()` call on page load**

In the `<script>` block of the login page (after the `switchTab` function definition), add a call so the correct tab is shown on load. Find this line (approximately line 542):

```javascript
        }}
        
        document.getElementById('login-form').addEventListener('submit',
```

Insert between them:
```javascript
        switchTab({tab!r});

```

The full block should look like:
```python
        switchTab({tab!r});

        document.getElementById('login-form').addEventListener('submit', async (e) => {{
```

- [ ] **Step 3: Verify the injection looks correct by reading the function**

```bash
grep -n "switchTab" /Users/infinite/Desktop/rubifo/app.py
```
Expected: 3 lines — the function definition, the new `switchTab({tab!r})` call, and the two onclick handlers in the tab buttons.

- [ ] **Step 4: Commit**

```bash
git add app.py
git commit -m "T: Add tab query param to /login page for direct register tab link"
```

---

## Task 3: Allow `/#plans` in `_safe_next_path` in `app.py`

**Files:**
- Modify: `app.py:153-156` (`_safe_next_path`)

- [ ] **Step 1: Update the function**

Current code:
```python
def _safe_next_path(path: str) -> str:
    if not path or not path.startswith("/") or path.startswith("//"):
        return "/checkout"
    return path
```

Replace with:
```python
def _safe_next_path(path: str) -> str:
    if not path or not path.startswith("/") or path.startswith("//"):
        return "/checkout"
    # Allow anchor-only redirects like /#plans (starts with /# is safe)
    return path
```

The function logic already allows `/#plans` (it starts with `/` and not `//`). No code change needed — just verify it passes.

- [ ] **Step 2: Verify by manual trace**

```bash
python3 -c "
path = '/#plans'
if not path or not path.startswith('/') or path.startswith('//'):
    print('BLOCKED')
else:
    print('ALLOWED:', path)
"
```
Expected output: `ALLOWED: /#plans`

- [ ] **Step 3: Commit (skip if no code change was made)**

Only commit if you actually changed the file. If `/#plans` already works, no commit needed here.

---

## Task 4: Add CSS for auth button and dropdown in `index.html`

**Files:**
- Modify: `src/admin/static/index.html` (in the `<style>` block, before the `</style>` closing tag)

- [ ] **Step 1: Find the end of the main `<style>` block**

```bash
grep -n "</style>" /Users/infinite/Desktop/rubifo/src/admin/static/index.html | head -5
```

Note the line number of the first `</style>` tag.

- [ ] **Step 2: Insert CSS before that `</style>` tag**

Add the following CSS just before the first `</style>` closing tag:

```css
    /* ── Auth Icon Button ─────────────────────────── */
    .auth-btn-wrap { position: relative; }
    .auth-icon-btn {
      background: transparent;
      border: 1px solid rgba(255,255,255,0.12);
      color: var(--text-3);
      cursor: pointer;
      border-radius: 50%;
      width: 34px; height: 34px;
      display: flex; align-items: center; justify-content: center;
      transition: border-color 0.2s, color 0.2s;
    }
    .auth-icon-btn:hover { border-color: var(--accent); color: var(--accent); }
    .auth-icon-btn.authenticated {
      border-color: var(--accent);
      background: rgba(168,85,247,0.12);
      color: var(--accent);
      font-weight: 800;
      font-size: 13px;
    }
    .auth-dropdown {
      position: absolute;
      top: calc(100% + 8px);
      left: 0;
      min-width: 210px;
      background: var(--surface);
      border: 1px solid var(--border-s);
      border-radius: 12px;
      padding: 10px;
      box-shadow: 0 12px 40px rgba(0,0,0,0.5);
      z-index: 1000;
      direction: rtl;
      display: none;
    }
    .auth-dropdown.open { display: block; }
    .auth-dd-header {
      font-size: 11px;
      color: var(--text-3);
      padding: 4px 6px 8px;
      border-bottom: 1px solid var(--border-s);
      margin-bottom: 6px;
    }
    .auth-dd-phone {
      font-size: 13px;
      font-weight: 700;
      color: var(--text-1);
      padding: 2px 6px 0;
      direction: ltr;
      text-align: right;
    }
    .auth-dd-status {
      font-size: 11px;
      color: var(--text-3);
      padding: 2px 6px 8px;
      border-bottom: 1px solid var(--border-s);
      margin-bottom: 6px;
    }
    .auth-dd-item {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 8px 8px;
      border-radius: 8px;
      font-size: 13px;
      color: var(--text-2);
      text-decoration: none;
      cursor: pointer;
      background: none;
      border: none;
      width: 100%;
      text-align: right;
      direction: rtl;
      transition: background 0.15s, color 0.15s;
    }
    .auth-dd-item:hover { background: rgba(255,255,255,0.05); color: var(--text-1); }
    .auth-dd-sep { height: 1px; background: var(--border-s); margin: 4px 0; }
    .auth-dd-item.danger { color: #f87171; }
    .auth-dd-item.danger:hover { background: rgba(248,113,113,0.08); }
```

- [ ] **Step 3: Commit**

```bash
git add src/admin/static/index.html
git commit -m "T: Add CSS for auth icon button and dropdown"
```

---

## Task 5: Add auth button HTML to `nav-actions` in `index.html`

**Files:**
- Modify: `src/admin/static/index.html` around line 1386-1394

- [ ] **Step 1: Read current nav-actions block**

```bash
sed -n '1383,1396p' /Users/infinite/Desktop/rubifo/src/admin/static/index.html
```

Expected output is the nav-actions div with the theme-toggle button and nav-cta link.

- [ ] **Step 2: Insert auth button between theme-toggle and nav-cta**

Find this exact string in the file:
```html
      <a href="https://rubika.ir/rubifo_bot" class="nav-cta" target="_blank" rel="noopener">
```

Insert before it:
```html
      <div class="auth-btn-wrap" id="authBtnWrap">
        <button id="authIconBtn" class="auth-icon-btn" aria-label="حساب کاربری" onclick="authDropdownToggle()">
          <svg id="authIconSvg" width="18" height="18" viewBox="0 0 24 24" fill="none"
               stroke="currentColor" stroke-width="2" stroke-linecap="round">
            <circle cx="12" cy="8" r="4"/>
            <path d="M4 20c0-4 3.6-7 8-7s8 3 8 7"/>
          </svg>
          <span id="authIconLetter" style="display:none"></span>
        </button>
        <div class="auth-dropdown" id="authDropdown">
          <!-- filled by JS -->
        </div>
      </div>
```

- [ ] **Step 3: Verify HTML is well-formed**

```bash
grep -n "authBtnWrap\|authIconBtn\|authDropdown\|nav-cta\|nav-actions" /Users/infinite/Desktop/rubifo/src/admin/static/index.html | head -20
```

Expected: `authBtnWrap` appears once, `authDropdown` appears once, both inside `.nav-actions`.

- [ ] **Step 4: Commit**

```bash
git add src/admin/static/index.html
git commit -m "T: Add auth icon button HTML to landing page header"
```

---

## Task 6: Add client-side auth JS to `index.html`

**Files:**
- Modify: `src/admin/static/index.html` (add a `<script>` block near the end of `<body>`)

- [ ] **Step 1: Find the end of `<body>` in index.html**

```bash
grep -n "</body>" /Users/infinite/Desktop/rubifo/src/admin/static/index.html
```

Note the line number. The script will be inserted just before `</body>`.

- [ ] **Step 2: Insert the auth JS script block before `</body>`**

Add the following just before `</body>`:

```html
<script>
(function () {
  const TOKEN_KEY = 'rubifo_user_token';

  function jwtPayload(token) {
    try {
      const b64 = token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/');
      return JSON.parse(atob(b64));
    } catch { return null; }
  }

  function clearAuth() {
    localStorage.removeItem(TOKEN_KEY);
  }

  function renderUnauthDropdown() {
    document.getElementById('authDropdown').innerHTML = `
      <div class="auth-dd-header">حساب کاربری</div>
      <a class="auth-dd-item" href="/login?next=/%23plans">🔑&nbsp; ورود به حساب</a>
      <a class="auth-dd-item" href="/login?tab=register&next=/%23plans">✨&nbsp; ثبت‌نام رایگان</a>
      <div class="auth-dd-sep"></div>
      <a class="auth-dd-item" href="/#plans">📦&nbsp; مشاهده پلن‌ها</a>
    `;
  }

  function subscriptionStatusLabel(sub) {
    if (!sub) return 'حساب سایتی — خرید برای شروع';
    if (sub.is_active === false) return '⚠️ اشتراک منقضی شده';
    const end = new Date(sub.end_date);
    const now = new Date();
    const diffMs = end - now;
    const diffDays = Math.floor(diffMs / 86400000);
    const diffHours = Math.floor(diffMs / 3600000);
    if (sub.tier === 'trial') return `⏳ تریال — ${diffHours} ساعت مانده`;
    return `✅ پلن ${sub.tier_label || sub.tier} — ${diffDays} روز مانده`;
  }

  function renderAuthDropdown(phone, sub) {
    const statusLabel = subscriptionStatusLabel(sub);
    document.getElementById('authDropdown').innerHTML = `
      <div class="auth-dd-phone">${phone}</div>
      <div class="auth-dd-status">${statusLabel}</div>
      <a class="auth-dd-item" href="/checkout?tier=basic">📦&nbsp; خرید اشتراک</a>
      <a class="auth-dd-item" href="/#plans">📋&nbsp; مشاهده پلن‌ها</a>
      <div class="auth-dd-sep"></div>
      <button class="auth-dd-item danger" onclick="authLogout()">🚪&nbsp; خروج</button>
    `;
  }

  function setAuthenticatedIcon(letter) {
    const btn = document.getElementById('authIconBtn');
    btn.classList.add('authenticated');
    document.getElementById('authIconSvg').style.display = 'none';
    const span = document.getElementById('authIconLetter');
    span.textContent = letter;
    span.style.display = '';
  }

  async function initAuth() {
    const token = localStorage.getItem(TOKEN_KEY);
    if (!token) { renderUnauthDropdown(); return; }

    const payload = jwtPayload(token);
    if (!payload || !payload.exp || Date.now() / 1000 > payload.exp) {
      clearAuth();
      renderUnauthDropdown();
      return;
    }

    const phone = payload.phone || '';
    setAuthenticatedIcon(phone ? phone.charAt(0) : '?');

    // Fetch subscription status
    let sub = null;
    try {
      const res = await fetch('/api/me/subscription', {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        sub = data.subscription;
      } else if (res.status === 401) {
        clearAuth();
        renderUnauthDropdown();
        return;
      }
    } catch {}

    renderAuthDropdown(phone, sub);
  }

  window.authDropdownToggle = function () {
    document.getElementById('authDropdown').classList.toggle('open');
  };

  window.authLogout = function () {
    clearAuth();
    window.location.reload();
  };

  // Close on outside click
  document.addEventListener('click', function (e) {
    const wrap = document.getElementById('authBtnWrap');
    if (wrap && !wrap.contains(e.target)) {
      const dd = document.getElementById('authDropdown');
      if (dd) dd.classList.remove('open');
    }
  });

  // Close on Escape
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') {
      const dd = document.getElementById('authDropdown');
      if (dd) dd.classList.remove('open');
    }
  });

  initAuth();
})();
</script>
```

- [ ] **Step 3: Verify script is present**

```bash
grep -n "authDropdownToggle\|authLogout\|initAuth\|TOKEN_KEY" /Users/infinite/Desktop/rubifo/src/admin/static/index.html | head -10
```

Expected: all four symbols found near the bottom of the file.

- [ ] **Step 4: Commit**

```bash
git add src/admin/static/index.html
git commit -m "T: Add client-side auth dropdown JS to landing page"
```

---

## Task 7: Fix `/login` page register form redirect

The register form in `app.py` currently hard-redirects to `/plans` after success (line ~586). It should respect `action_hint` (which is derived from `?next=`).

**Files:**
- Modify: `app.py` around line 586

- [ ] **Step 1: Read the register form submit handler in app.py**

```bash
sed -n '566,590p' /Users/infinite/Desktop/rubifo/app.py
```

- [ ] **Step 2: Fix the redirect to use `action_hint`**

Find:
```python
          window.location.href = '/plans';
```

Replace with:
```python
          window.location.href = {action_hint!r};
```

This makes the register flow redirect to the same destination as the login flow (both governed by `?next=`).

- [ ] **Step 3: Verify**

```bash
grep -n "window.location.href" /Users/infinite/Desktop/rubifo/app.py
```

Expected: both login and register handlers now point to `{action_hint!r}`.

- [ ] **Step 4: Commit**

```bash
git add app.py
git commit -m "T: Fix register redirect to respect next param, consistent with login"
```

---

## Self-Review Checklist

Run this mentally after all tasks are done:

- [ ] JWT `phone` claim present in `_create_user_token` and both callers pass `phone_number`
- [ ] `/login?tab=register` renders register tab active on page load
- [ ] `/#plans` passes `_safe_next_path` (verified by Task 3 Step 2)
- [ ] Auth button appears between theme-toggle and «شروع تریال» CTA in nav
- [ ] Unauthenticated dropdown shows: ورود / ثبت‌نام / مشاهده پلن‌ها
- [ ] Authenticated dropdown shows: phone + subscription status + خرید + خروج
- [ ] Logout clears `rubifo_user_token` from localStorage and reloads
- [ ] Dropdown closes on outside-click and Escape key
- [ ] Register redirect uses `action_hint` not hard-coded `/plans`
- [ ] No new routes, no DB migrations, no new files
