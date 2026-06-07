# Header Auth Dropdown — Design Spec

**Date:** 2026-06-07
**Status:** Approved

---

## Goal

Add a user account entry point to the landing page header so visitors can register, log in, and reach the plans section without going through the Rubika bot first.

---

## Design Decisions

| Decision | Choice |
|----------|--------|
| Header element | Minimal profile icon (no text label) |
| Interaction pattern | Smart dropdown |
| Unauthenticated state | Links: ورود / ثبت‌نام / مشاهده پلن‌ها |
| Authenticated state | Phone + subscription status + خرید + خروج |
| Post-register redirect | `/#plans` (scroll to plans section in landing) |
| Post-login redirect | `/#plans` |

---

## Header Changes (`src/admin/static/index.html`)

Add the profile icon button **between** the theme-toggle button and the «شروع تریال» CTA inside `.nav-actions`.

```html
<button id="auth-icon-btn" class="auth-icon-btn" aria-label="حساب کاربری">
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none"
       stroke="currentColor" stroke-width="2" stroke-linecap="round">
    <circle cx="12" cy="8" r="4"/>
    <path d="M4 20c0-4 3.6-7 8-7s8 3 8 7"/>
  </svg>
</button>
```

When the user is authenticated (JWT found in `localStorage`), the button gets an `.authenticated` class: purple ring border + first letter of phone number as avatar text instead of the SVG icon.

---

## Dropdown Component

A floating panel that opens below the icon button on click, closes on outside-click or Escape.

### Unauthenticated state

```
┌─────────────────────────────┐
│ حساب کاربری                │  ← small label
├─────────────────────────────┤
│ 🔑  ورود به حساب           │  → /login
│ ✨  ثبت‌نام رایگان         │  → /login (register tab active)
├─────────────────────────────┤
│ 📦  مشاهده پلن‌ها          │  → /#plans
└─────────────────────────────┘
```

### Authenticated state

```
┌─────────────────────────────┐
│ ⬤  09123456789             │  ← avatar + phone from JWT/API
│    ⏳ تریال — ۶۵ ساعت مانده│  ← subscription status (live from /api/me/subscription)
├─────────────────────────────┤
│ 📦  خرید اشتراک            │  → /checkout?tier=basic
│ 📋  مشاهده پلن‌ها          │  → /#plans
├─────────────────────────────┤
│ 🚪  خروج                   │  → clears localStorage, reloads
└─────────────────────────────┘
```

Subscription status label logic:
- `trial` → `⏳ تریال — {hours_left} ساعت مانده`
- `active` → `✅ پلن {tier_name} — {days_left} روز مانده`
- `expired` → `⚠️ اشتراک منقضی شده`
- No subscription yet (web user, no trial started) → `حساب سایتی — خرید برای شروع`

---

## Authentication Logic (client-side JS in index.html)

On page load:

```js
const token = localStorage.getItem('rubifo_user_token');
if (token) {
  // 1. Decode JWT payload (base64, no verify — server validates on API calls)
  // 2. Extract sub (user_id) and exp
  // 3. If expired → clear token, show unauthenticated state
  // 4. If valid → fetch /api/me/subscription with Bearer token
  //    → render authenticated dropdown with phone + subscription status
}
```

Phone number: stored in JWT or fetched from `/api/me/subscription` response. The existing `/api/me/subscription` endpoint returns subscription data but not phone. We need either:
- Store phone in JWT at login/register time (add `phone` claim)
- Or add a `/api/me/profile` endpoint

**Decision:** Add `phone_number` to the JWT payload at token creation so no extra API call is needed for basic display. The subscription status still requires a fetch to `/api/me/subscription`.

---

## Backend Changes (`app.py`)

### 1. Add `phone_number` to JWT payload

In `_create_user_token(user_id)`, the function currently takes only `user_id`. Change signature to also accept `phone_number` and add it to the payload:

```python
def _create_user_token(user_id: str, phone_number: str = "") -> str:
    payload = {
        "scope": "web_user",
        "sub": user_id,
        "phone": phone_number,   # ← new
        "exp": ...,
        "iat": ...,
    }
```

Update callers: `web_user_login` and `web_user_register` both pass `user.phone_number`.

### 2. `/login` page — open register tab via query param

`GET /login?tab=register` → the tabbed login page should default to the register tab when this param is present. The existing `web_login_page` function needs a `tab: str = "login"` param and injects it into the JS `switchTab()` call on load.

---

## Post-Register / Post-Login Redirect

Both the register and login form submissions in `/login` currently redirect to `action_hint` (defaults to `/checkout`).

For the new flow from the landing page:
- Links from the dropdown pass `?next=/#plans` → after auth, redirect to `/#plans`
- Links from the checkout button (existing flow) still pass `?next=/checkout&tier=...`

The `_safe_next_path()` function currently only allows paths starting with `/`. The `/#plans` anchor redirect needs handling: treat `/#plans` as a valid next path (it starts with `/`).

---

## Styling

New CSS in `index.html`:

```css
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
  left: 0;            /* RTL: aligns to left edge of button */
  min-width: 200px;
  background: var(--surface);
  border: 1px solid var(--border-s);
  border-radius: 12px;
  padding: 10px;
  box-shadow: 0 12px 40px rgba(0,0,0,0.5);
  z-index: 1000;
  direction: rtl;
}
```

The button's parent gets `position: relative` to anchor the dropdown.

---

## Files Changed

| File | Change |
|------|--------|
| `src/admin/static/index.html` | Add auth icon button + dropdown CSS + client JS |
| `app.py` | Add `phone` claim to JWT, add `tab` param to `/login`, update `_safe_next_path` |

No new routes, no DB changes, no migration needed.

---

## Out of Scope

- User profile/settings page
- Password change from landing
- Social login
- Email verification
