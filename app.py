"""
ParsPackPaaS entry point — combined FastAPI app.

All three services run in one process on one port:
  Landing page   GET  /
  Admin panel    GET  /admin/*   POST /admin/login
  Bot webhook    POST /webhook
  Health check   GET  /health

Run:
  uvicorn app:app --host 0.0.0.0 --port $PORT
or:
  python app.py
"""
import asyncio
import os
from html import escape
from pathlib import Path
from pydantic import BaseModel
from jose import JWTError, jwt
from fastapi import FastAPI, Depends, HTTPException, Request, status
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, PlainTextResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.staticfiles import StaticFiles
import src.database as db_module
from src.config import (
    OUTBOUND_IP_CHECK_ENABLED,
    RUBIKA_BOT_RETURN_URL,
    SUBSCRIPTION_TIERS,
    USER_JWT_SECRET,
    WEB_BASE_URL,
)
from src.core.outbound_ip_monitor import OutboundIPMonitor
from src.core.subscription_service import SubscriptionService
from src.core.settings_service import SettingsService
from src.core.transaction_service import TransactionService
from src.core.user_service import UserService
from src.integrations.zibal import create_zibal_gateway
from src.integrations.zibal_mock import create_zibal_mock_gateway
from src.logger import logger
from src.utils import to_jalali_date

_STATIC_DIR = Path(__file__).parent / "src" / "admin" / "static"
_ENAMAD_VERIFICATION_FILE = Path(__file__).parent / "795459943.txt"
_ENAMAD_LEGACY_VERIFICATION_FILE = Path(__file__).parent / "79545943.txt"

app = FastAPI(title="Rubifo", docs_url=None, redoc_url=None)

# ─────────────────────────────────────────────────────────────
# Static assets
# ─────────────────────────────────────────────────────────────
app.mount("/static", StaticFiles(directory=_STATIC_DIR), name="static")
app.mount("/fonts", StaticFiles(directory=_STATIC_DIR / "fonts"), name="fonts")

# ─────────────────────────────────────────────────────────────
# Admin API routes  (/admin/*)
# ─────────────────────────────────────────────────────────────
from src.admin import routes as _admin_routes
from src.admin.auth import verify_token, auth_service

app.include_router(_admin_routes.router)


class _LoginBody(BaseModel):
    username: str
    password: str


class _UserLoginBody(BaseModel):
    phone_number: str
    password: str


class _UserRegisterBody(BaseModel):
    phone_number: str
    password: str
    confirm_password: str


class _CheckoutStartBody(BaseModel):
    tier: str
    months: int = 1


@app.post("/admin/login")
async def admin_login(body: _LoginBody):
    token = auth_service.authenticate(body.username, body.password)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="نام کاربری یا رمز عبور اشتباه است")
    return {"access_token": token, "token_type": "bearer"}


# ─────────────────────────────────────────────────────────────
# Website user auth + checkout
# ─────────────────────────────────────────────────────────────
_user_security = HTTPBearer()
_USER_TOKEN_ALG = "HS256"
_USER_TOKEN_EXP_HOURS = 24 * 14


def _web_db():
    if db_module.pool is None:
        raise HTTPException(status_code=503, detail="Database is not ready")
    return db_module.pool


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


async def _current_web_user(
    credentials: HTTPAuthorizationCredentials = Depends(_user_security),
):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, USER_JWT_SECRET, algorithms=[_USER_TOKEN_ALG])
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    if payload.get("scope") != "web_user" or not payload.get("sub"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user = await UserService(_web_db()).get_user(payload["sub"])
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


def _format_toman(amount: int) -> str:
    return f"{amount:,}".replace(",", "،")


def _tier_label(tier: str) -> str:
    return SUBSCRIPTION_TIERS.get(tier, {}).get("display_name_fa", tier)


_CHECKOUT_MONTH_OPTIONS = (1, 3, 6, 12)


def _checkout_months_from_amount(tier: str, amount: int) -> int:
    monthly_price = SUBSCRIPTION_TIERS.get(tier, {}).get("price_monthly", 0)
    if monthly_price <= 0 or amount % monthly_price != 0:
        return 1
    months = amount // monthly_price
    return months if months in _CHECKOUT_MONTH_OPTIONS else 1


def _safe_next_path(path: str) -> str:
    if not path or not path.startswith("/") or path.startswith("//"):
        return "/checkout"
    return path


def _html_page(title: str, body: str, page_class: str = "") -> HTMLResponse:
    return HTMLResponse(
        f"""<!doctype html>
<html lang="fa" dir="rtl">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  <script>
    (() => {{
      const saved = localStorage.getItem('rubifo-theme');
      document.documentElement.setAttribute('data-theme', saved === 'light' ? 'light' : 'dark');
    }})();
  </script>
  <style>
    @font-face {{ font-family: 'Morabba'; src: url('/fonts/Morabba-Regular.woff2') format('woff2'); font-weight: 400; font-display: swap; }}
    @font-face {{ font-family: 'Morabba'; src: url('/fonts/Morabba-SemiBold.woff2') format('woff2'); font-weight: 600; font-display: swap; }}
    @font-face {{ font-family: 'Morabba'; src: url('/fonts/Morabba-ExtraBold.woff2') format('woff2'); font-weight: 800; font-display: swap; }}
    @font-face {{ font-family: 'Vazirmatn'; src: url('/fonts/Vazirmatn-Regular.woff2') format('woff2'); font-weight: 400; font-display: swap; }}
    @font-face {{ font-family: 'Vazirmatn'; src: url('/fonts/Vazirmatn-Bold.woff2') format('woff2'); font-weight: 700; font-display: swap; }}
    :root {{
      --black:    #050507;
      --black-2:  #09090f;
      --black-3:  #0d0d18;
      --black-4:  #111120;
      --purple:   #5B2E8A;
      --purple-m: #7B3FAE;
      --purple-d: #3A1A5E;
      --violet:   #A855F7;
      --violet-l: #C084FC;
      --violet-d: #8B5CF6;
      --emerald:  #10B981;
      --gold:     #F59E0B;
      --t1:       #F3F0FF;
      --t2:       #C4B5FD;
      --t3:       #8B7EC8;
      --t4:       rgba(139,126,200,0.45);
      --border:   rgba(168,85,247,0.12);
      --border-s: rgba(168,85,247,0.24);
      --border-m: rgba(168,85,247,0.40);

      --bg: var(--black);
      --surface: rgba(13,13,24,0.82);
      --surface-2: rgba(17,17,32,0.78);
      --surface-3: rgba(31,25,51,0.78);
      --text: var(--t1);
      --text-2: var(--t2);
      --text-3: var(--t3);
      --accent: var(--violet);
      --accent-dark: var(--violet-d);
      --accent-subtle: rgba(168,85,247,0.10);
      --ok: var(--emerald);
      --err: #FB7185;
      --warn: var(--gold);
      --border-soft: var(--border);
    }}
    html[data-theme="light"] {{
      --black:    #F5F2FF;
      --black-2:  #EBE6FA;
      --black-3:  #FFFFFF;
      --black-4:  #DED6F5;
      --t1:       #0D0820;
      --t2:       #2A1D52;
      --t3:       #5A4A8A;
      --t4:       rgba(60,44,110,0.45);
      --border:   rgba(100,50,200,0.16);
      --border-s: rgba(100,50,200,0.30);
      --border-m: rgba(100,50,200,0.52);
      --surface: rgba(255,255,255,0.70);
      --surface-2: rgba(255,255,255,0.54);
      --surface-3: rgba(235,230,250,0.86);
      --accent-subtle: rgba(123,58,237,0.08);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      min-height: 100vh;
      font-family: 'Morabba', 'Vazirmatn', system-ui, sans-serif;
      background:
        radial-gradient(ellipse 64% 48% at 74% 14%, rgba(168,85,247,0.18), transparent 68%),
        radial-gradient(ellipse 42% 38% at 12% 90%, rgba(91,46,138,0.22), transparent 62%),
        var(--bg);
      color: var(--text);
      line-height: 1.8;
    }}
    html[data-theme="light"] body {{
      background:
        radial-gradient(ellipse 64% 48% at 74% 14%, rgba(168,85,247,0.16), transparent 68%),
        radial-gradient(ellipse 42% 38% at 12% 90%, rgba(91,46,138,0.10), transparent 62%),
        var(--bg);
    }}
    a {{ color: inherit; }}
    .checkout-shell {{
      width: min(1120px, calc(100% - 32px));
      min-height: 100vh;
      margin: 0 auto;
      display: grid;
      align-items: center;
      padding: 40px 0;
    }}
    .checkout-frame {{
      display: grid;
      grid-template-columns: minmax(0, 1.05fr) minmax(320px, 0.95fr);
      gap: clamp(20px, 4vw, 48px);
      align-items: stretch;
    }}
    .checkout-copy {{
      display: flex;
      flex-direction: column;
      justify-content: center;
      gap: 22px;
      min-width: 0;
    }}
    .brand-mark {{
      display: inline-flex;
      align-items: center;
      gap: 10px;
      color: var(--accent);
      font-weight: 800;
      font-size: 15px;
    }}
    .brand-mark::before {{
      content: "";
      width: 10px;
      height: 10px;
      border-radius: 999px;
      background: var(--accent);
      box-shadow: 0 0 0 5px rgba(168,85,247,0.14);
    }}
    h1 {{
      margin: 0;
      max-width: 12ch;
      font-size: clamp(38px, 7vw, 78px);
      line-height: 1.12;
      font-weight: 800;
      letter-spacing: 0;
    }}
    .lead {{
      max-width: 58ch;
      margin: 0;
      color: var(--text-2);
      font-size: 16px;
    }}
    .checkout-panel {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 16px;
      padding: clamp(22px, 4vw, 34px);
      box-shadow: inset 0 1px 0 rgba(255,255,255,0.05), 0 16px 60px rgba(0,0,0,0.42);
      backdrop-filter: blur(22px);
    }}
    html[data-theme="light"] .checkout-panel {{
      box-shadow: inset 0 1px 0 rgba(255,255,255,0.9), 0 18px 56px rgba(91,46,138,0.14);
    }}
    .panel-kicker {{
      margin-bottom: 8px;
      color: var(--accent);
      font-size: 12px;
      font-weight: 800;
    }}
    .panel-title {{
      margin: 0 0 16px;
      font-size: 25px;
      line-height: 1.35;
      font-weight: 800;
    }}
    .field {{ margin: 0 0 14px; }}
    label {{
      display: block;
      margin-bottom: 7px;
      color: var(--text-2);
      font-size: 13px;
      font-weight: 700;
    }}
    input, select {{
      width: 100%;
      border: 1px solid var(--border);
      border-radius: 8px;
      background: var(--surface-2);
      color: var(--text);
      padding: 12px 13px;
      font: inherit;
      outline: none;
    }}
    input:focus, select:focus {{
      border-color: var(--accent);
      box-shadow: 0 0 0 3px rgba(168,85,247,0.24);
    }}
    .button-row {{
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      align-items: center;
      margin-top: 18px;
    }}
    .btn {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-height: 44px;
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 10px 17px;
      font: inherit;
      font-weight: 800;
      text-decoration: none;
      cursor: pointer;
      transition: transform 150ms ease-out, background 150ms ease-out, border-color 150ms ease-out;
    }}
    .btn:hover {{ transform: translateY(-1px); }}
    .btn-primary {{
      background: var(--accent);
      border-color: var(--accent);
      color: #fff;
      box-shadow: inset 0 1px 0 rgba(255,255,255,0.20), 0 8px 24px rgba(91,46,138,0.36);
    }}
    .btn-primary:hover {{ background: var(--accent-dark); border-color: var(--accent-dark); }}
    .btn-ghost {{ background: transparent; color: var(--text-2); }}
    .btn-ghost:hover {{ background: var(--surface-2); color: var(--text); }}
    .btn-danger {{ background: rgba(244,63,94,0.10); border-color: rgba(244,63,94,0.32); color: var(--err); }}
    .btn-warn {{ background: rgba(245,158,11,0.10); border-color: rgba(245,158,11,0.32); color: var(--warn); }}
    .summary {{
      display: grid;
      gap: 10px;
      margin: 18px 0;
      padding: 16px;
      background: var(--surface-2);
      border: 1px solid var(--border-soft);
      border-radius: 10px;
    }}
    .summary-row {{
      display: flex;
      justify-content: space-between;
      gap: 16px;
      color: var(--text-2);
      font-size: 14px;
    }}
    .summary-row strong {{ color: var(--text); }}
    .error-note {{
      min-height: 24px;
      margin: 12px 0 0;
      color: var(--err);
      font-size: 13px;
      font-weight: 700;
    }}
    .hint-box {{
      margin-top: 18px;
      padding: 14px 15px;
      border-radius: 10px;
      background: var(--accent-subtle);
      color: var(--text-2);
      border: 1px solid var(--border-s);
      font-size: 14px;
    }}
    .status-box {{
      margin: 14px 0 0;
      padding: 13px 14px;
      border-radius: 8px;
      background: rgba(16,185,129,0.08);
      border: 1px solid rgba(16,185,129,0.24);
      color: var(--text-2);
      font-size: 14px;
    }}
    .status-box[data-mode="change"] {{
      background: rgba(245,158,11,0.08);
      border-color: rgba(245,158,11,0.24);
    }}
    .status-box[hidden] {{ display: none; }}
    .status-chip {{
      display: inline-flex;
      width: fit-content;
      border: 1px solid var(--border);
      border-radius: 999px;
      padding: 5px 10px;
      color: var(--text-2);
      background: var(--surface-2);
      font-size: 12px;
      font-weight: 800;
    }}
    .success h1 {{ color: var(--ok); }}
    .failure h1 {{ color: var(--err); }}
    .canceled h1 {{ color: var(--warn); }}
    @media (max-width: 820px) {{
      .checkout-frame {{ grid-template-columns: 1fr; }}
      h1 {{ max-width: 100%; font-size: 42px; }}
      .checkout-shell {{ align-items: start; padding-top: 28px; }}
    }}
  </style>
</head>
<body class="{escape(page_class)}">
  <main class="checkout-shell">
    <section class="checkout-frame">
      {body}
    </section>
  </main>
</body>
</html>"""
    )


@app.get("/login")
async def web_login_page(next: str = "/checkout", tier: str = "", tab: str = "login"):
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
        switchTab({tab!r});

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
          window.location.href = {action_hint!r};
        }});
        </script>
        """,
        page_class="login-page",
    )


@app.post("/api/auth/login")
async def web_user_login(body: _UserLoginBody):
    try:
        user = await UserService(_web_db()).authenticate_web_user(
            body.phone_number, body.password
        )
    except ValueError:
        user = None
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="ورود انجام نشد. اول داخل ربات ثبت‌نام کنید و رمز ورود بسازید.",
        )

    return {
        "access_token": _create_user_token(user.user_id, user.phone_number or ""),
        "token_type": "bearer",
        "user": {
            "user_id": user.user_id,
            "username": user.username,
            "phone_number": user.phone_number,
        },
    }


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
        "access_token": _create_user_token(user.user_id, user.phone_number or ""),
        "token_type": "bearer",
        "user": {
            "user_id": user.user_id,
            "phone_number": user.phone_number,
        },
    }


@app.get("/api/plans")
async def public_plans():
    """Public endpoint returning current plan prices from DB."""
    tiers = await SettingsService(_web_db()).get_plans()
    return {
        tier: {
            "name": cfg["display_name_fa"],
            "price_monthly": cfg["price_monthly"],
            "max_destinations": cfg["max_destinations"],
        }
        for tier, cfg in tiers.items()
    }


@app.get("/api/me/subscription")
async def web_user_subscription(user=Depends(_current_web_user)):
    subscription = await SubscriptionService(_web_db()).get_active_subscription(user.user_id)
    if not subscription:
        return {"subscription": None}
    return {
        "subscription": {
            "tier": subscription.tier,
            "tier_label": _tier_label(subscription.tier),
            "start_date": subscription.start_date.isoformat(),
            "end_date": subscription.end_date.isoformat(),
            "is_active": subscription.is_active,
        }
    }


@app.get("/checkout")
async def checkout_page(tier: str = "basic"):
    tiers = await SettingsService(_web_db()).get_plans()
    if tier not in tiers:
        return _html_page(
            "پلن نامعتبر",
            f"""
            <div class="checkout-copy">
              <div class="brand-mark">Rubifo checkout</div>
              <h1>این پلن را نمی‌شناسیم.</h1>
              <p class="lead">برای انتخاب مطمئن، به بخش پلن‌های اشتراک برگردید و یکی از بسته‌های فعال روبیفو را انتخاب کنید.</p>
            </div>
            <div class="checkout-panel">
              <div class="panel-kicker">پلن نامعتبر</div>
              <h2 class="panel-title">پلن‌های اشتراک آماده‌اند</h2>
              <p class="lead">شروع حرفه‌ای، رشد و مقیاس مسیرهای فعال خرید هستند.</p>
              <div class="button-row">
                <a class="btn btn-primary" href="/#plans">دیدن پلن‌های اشتراک</a>
                <a class="btn btn-ghost" href="{RUBIKA_BOT_RETURN_URL}">رفتن به ربات</a>
              </div>
            </div>
            """,
            page_class="failure",
        )

    cfg = tiers[tier]
    tier_name = cfg["display_name_fa"]
    price = _format_toman(cfg["price_monthly"])
    destinations = cfg["max_destinations"]
    month_options = "".join(
        f'<option value="{months}">{months} ماهه</option>'
        for months in _CHECKOUT_MONTH_OPTIONS
    )
    return _html_page(
        "خرید اشتراک Rubifo",
        f"""
        <div class="checkout-copy">
          <div class="brand-mark">Rubifo checkout</div>
          <h1>پلن را ببندیم، ربات شروع کند.</h1>
          <p class="lead">پرداخت امن از طریق درگاه زیبال. بعد از پرداخت، اشتراک فوری فعال می‌شود.</p>
          <span class="status-chip">درگاه زیبال</span>
        </div>
        <div class="checkout-panel">
          <div class="panel-kicker">خلاصه سفارش</div>
          <h2 class="panel-title">اشتراک {escape(tier_name)}</h2>
          <div class="summary">
            <div class="summary-row"><span>مبلغ ماهانه</span><strong>{price} تومان</strong></div>
            <div class="summary-row"><span>مدت اشتراک</span><strong id="months-label">1 ماهه</strong></div>
            <div class="summary-row"><span>مبلغ کل</span><strong id="total-amount">{price} تومان</strong></div>
            <div class="summary-row"><span>کانال مقصد</span><strong>{destinations}</strong></div>
            <div class="summary-row"><span>دسترسی</span><strong>همه قابلیت‌های انتشار</strong></div>
          </div>
          <input id="tier" type="hidden" value="{escape(tier)}">
          <input id="monthly-price" type="hidden" value="{cfg["price_monthly"]}">
          <div class="field">
            <label for="months">مدت اشتراک</label>
            <select id="months" name="months">
              {month_options}
            </select>
          </div>
          <div id="subscription-status" class="status-box" hidden
               data-renew-text="اشتراک فعال دارید؛ این خرید تمدید می‌شود."
               data-change-text="اشتراک فعال دارید؛ این خرید پلن شما را تغییر می‌دهد."></div>
          <button id="pay" class="btn btn-primary" type="button">پرداخت از طریق زیبال</button>
          <p id="checkout-error" class="error-note"></p>
          <div class="hint-box">بعد از پرداخت موفق، همین صفحه اشتراک را فعال می‌کند و لینک مستقیم شروع در ربات را نشان می‌دهد.</div>
        </div>
        <script>
        const tierInput = document.getElementById('tier');
        const monthsInput = document.getElementById('months');
        const monthlyPrice = Number(document.getElementById('monthly-price').value);
        const totalAmount = document.getElementById('total-amount');
        const monthsLabel = document.getElementById('months-label');
        const statusBox = document.getElementById('subscription-status');

        function formatToman(value) {{
          return new Intl.NumberFormat('fa-IR').format(value).replace(/٬/g, '،');
        }}

        function updateTotal() {{
          const months = Number(monthsInput.value);
          monthsLabel.textContent = months + ' ماهه';
          totalAmount.textContent = formatToman(monthlyPrice * months) + ' تومان';
        }}

        async function loadSubscriptionStatus() {{
          const token = localStorage.getItem('rubifo_user_token');
          if (!token) {{
            return;
          }}
          const res = await fetch('/api/me/subscription', {{
            headers: {{'Authorization': 'Bearer ' + token}}
          }});
          if (!res.ok) return;
          const data = await res.json();
          if (!data.subscription || !data.subscription.is_active) return;
          const sameTier = data.subscription.tier === tierInput.value;
          statusBox.textContent = sameTier ? statusBox.dataset.renewText : statusBox.dataset.changeText;
          statusBox.dataset.mode = sameTier ? 'renew' : 'change';
          statusBox.hidden = false;
        }}

        monthsInput.addEventListener('change', updateTotal);
        updateTotal();
        loadSubscriptionStatus();

        document.getElementById('pay').addEventListener('click', async () => {{
          const token = localStorage.getItem('rubifo_user_token');
          if (!token) {{
            window.location.href = '/login?next=/checkout&tier=' + encodeURIComponent(tierInput.value);
            return;
          }}
          const res = await fetch('/api/checkout/start', {{
            method: 'POST',
            headers: {{
              'Content-Type': 'application/json',
              'Authorization': 'Bearer ' + token
            }},
            body: JSON.stringify({{tier: tierInput.value, months: Number(monthsInput.value)}})
          }});
          if (res.status === 401) {{
            window.location.href = '/login?next=/checkout&tier=' + encodeURIComponent(tierInput.value);
            return;
          }}
          if (!res.ok) {{
            document.getElementById('checkout-error').textContent = 'شروع پرداخت ممکن نشد. دوباره تلاش کنید.';
            return;
          }}
          const data = await res.json();
          window.location.href = data.payment_url;
        }});
        </script>
        """,
        page_class="checkout-page",
    )


@app.post("/api/checkout/start")
async def checkout_start(body: _CheckoutStartBody, user=Depends(_current_web_user)):
    tiers = await SettingsService(_web_db()).get_plans()
    if body.tier not in tiers:
        raise HTTPException(status_code=400, detail="Invalid subscription tier")
    if body.months not in _CHECKOUT_MONTH_OPTIONS:
        raise HTTPException(status_code=400, detail="Invalid subscription duration")

    tier_config = tiers[body.tier]
    amount = tier_config["price_monthly"] * body.months
    callback_url = f"{WEB_BASE_URL.rstrip('/')}/payment/callback"
    gateway = create_zibal_gateway()
    success, result = await gateway.request_payment(
        amount=amount,
        description=f"اشتراک {tier_config['display_name_fa']} - Rubifo",
        callback_url=callback_url,
    )
    if not success:
        raise HTTPException(status_code=502, detail=result.get("message", "Payment failed"))

    authority = result["track_id"]
    await TransactionService(_web_db()).create_pending_transaction(
        user.user_id, amount, body.tier, authority
    )
    return {
        "payment_url": result["payment_url"],
        "track_id": authority,
        "authority": authority,
        "provider": result["provider"],
    }


@app.get("/mock/zibal/start/{track_id}")
async def mock_zibal_payment_page(track_id: str):
    safe_track = escape(track_id)
    return _html_page(
        "پرداخت تست زیبال",
        f"""
        <div class="checkout-copy">
          <div class="brand-mark">Zibal mock</div>
          <h1>اینجا درگاه تست است.</h1>
          <p class="lead">برای QA مسیر خرید، یکی از سه نتیجه پرداخت را انتخاب کنید. هیچ پولی جابه‌جا نمی‌شود.</p>
          <span class="status-chip">trackId: {safe_track}</span>
        </div>
        <div class="checkout-panel">
          <div class="panel-kicker">شبیه‌ساز پرداخت</div>
          <h2 class="panel-title">نتیجه تست را انتخاب کنید</h2>
          <div class="summary">
            <div class="summary-row"><span>درگاه</span><strong>زیبال موک</strong></div>
            <div class="summary-row"><span>شناسه پرداخت</span><strong>{safe_track}</strong></div>
          </div>
          <div class="button-row">
            <a class="btn btn-primary" href="/payment/callback?trackId={safe_track}&success=1">پرداخت موفق</a>
            <a class="btn btn-danger" href="/payment/callback?trackId={safe_track}&success=0">پرداخت ناموفق</a>
            <a class="btn btn-warn" href="/payment/callback?trackId={safe_track}&success=-1">لغو پرداخت</a>
          </div>
        </div>
        """,
        page_class="mock-payment-page",
    )


def _payment_result_page(
    title: str,
    message: str,
    *,
    ref_id: str = "",
    page_class: str = "",
    primary_label: str = "شروع در ربات",
) -> HTMLResponse:
    ref_markup = (
        f"""<div class="summary-row"><span>کد رهگیری</span><strong>{escape(ref_id)}</strong></div>"""
        if ref_id
        else ""
    )
    return _html_page(
        title,
        f"""
        <div class="checkout-copy">
          <div class="brand-mark">Rubifo checkout</div>
          <h1>{escape(title)}</h1>
          <p class="lead">{escape(message)}</p>
        </div>
        <div class="checkout-panel">
          <div class="panel-kicker">نتیجه پرداخت</div>
          <h2 class="panel-title">{escape(title)}</h2>
          <div class="summary">
            <div class="summary-row"><span>وضعیت</span><strong>{escape(title)}</strong></div>
            {ref_markup}
          </div>
          <div class="button-row">
            <a class="btn btn-primary" href="{RUBIKA_BOT_RETURN_URL}">{escape(primary_label)}</a>
            <a class="btn btn-ghost" href="/#plans">بازگشت به پلن‌ها</a>
          </div>
        </div>
        """,
        page_class=page_class,
    )


async def _notify_paid_user(
    user_id: str,
    tier: str,
    end_date,
    *,
    amount: int,
    ref_id: str,
) -> None:
    client = _bot_ref.client if _bot_ref else None
    if not client:
        logger.warning("Paid user notification skipped: bot client is unavailable")
        return
    tier_config = SUBSCRIPTION_TIERS[tier]
    tier_name = tier_config["display_name_fa"]
    destinations = tier_config["max_destinations"]
    amount_text = _format_toman(amount)
    try:
        from rubpy.bot.enums import ButtonTypeEnum
        from rubpy.bot.models import Button, Keypad, KeypadRow

        inline_keypad = Keypad(rows=[
            KeypadRow(buttons=[
                Button(
                    id="new_program",
                    type=ButtonTypeEnum.SIMPLE,
                    button_text="➕ ساخت برنامه جدید",
                )
            ])
        ])
        await client.send_message(
            user_id,
            "✅ پرداخت شما با موفقیت انجام شد.\n\n"
            "رسید پرداخت روبیفو\n"
            f"پلن: {tier_name}\n"
            f"مبلغ: {amount_text} تومان\n"
            f"کد رهگیری: {ref_id}\n"
            f"تاریخ پایان اشتراک: {to_jalali_date(end_date)}\n"
            f"ظرفیت پلن: {destinations} کانال مقصد\n\n"
            "برای شروع انتشار، دکمه ساخت برنامه جدید را بزنید.",
            inline_keypad=inline_keypad,
        )
    except Exception as exc:
        logger.warning(f"Paid user notification failed for {user_id}: {exc}")


async def _activate_paid_subscription(user_id: str, tier: str, amount: int):
    subscription_service = SubscriptionService(_web_db())
    months = _checkout_months_from_amount(tier, amount)
    days = months * 30
    active_subscription = await subscription_service.get_active_subscription(user_id)
    if active_subscription and active_subscription.tier == tier:
        return await subscription_service.extend_subscription(user_id, days=days)
    return await subscription_service.create_subscription(user_id, tier, days=days)


@app.get("/payment/callback")
async def payment_callback(
    trackId: str = "",
    success: str = "",
    Authority: str = "",
    Status: str = "",
):
    payment_id = trackId or Authority
    if not payment_id:
        return _payment_result_page(
            "پرداخت نامعتبر",
            "شناسه پرداخت از زیبال دریافت نشد.",
            page_class="failure",
            primary_label="رفتن به ربات",
        )

    transaction_service = TransactionService(_web_db())
    transaction = await transaction_service.get_transaction_by_authority(payment_id)
    if not transaction:
        return _payment_result_page(
            "پرداخت پیدا نشد",
            "این پرداخت در Rubifo ثبت نشده است.",
            page_class="failure",
            primary_label="رفتن به ربات",
        )

    if transaction.get("status") == "completed":
        ref = transaction.get("reference_id") or "ثبت‌شده"
        return _payment_result_page(
            "پرداخت قبلاً تأیید شده",
            "اشتراک شما قبلاً فعال شده است.",
            ref_id=ref,
            page_class="success",
        )

    if success == "-1" or (Status and Status.upper() not in {"OK", "NOK"}):
        await transaction_service.update_transaction_status(transaction["id"], "canceled")
        return _payment_result_page(
            "پرداخت لغو شد",
            "پرداخت از سمت درگاه لغو شد. هر وقت آماده بودید دوباره از پلن‌ها شروع کنید.",
            ref_id=payment_id,
            page_class="canceled",
            primary_label="رفتن به ربات",
        )

    if success and success != "1":
        await transaction_service.update_transaction_status(transaction["id"], "failed")
        return _payment_result_page(
            "پرداخت ناموفق",
            "تأیید پرداخت انجام نشد. اشتراک فعال نشد و می‌توانید دوباره تلاش کنید.",
            ref_id=payment_id,
            page_class="failure",
            primary_label="رفتن به ربات",
        )

    if Authority and Status.upper() != "OK":
        await transaction_service.update_transaction_status(transaction["id"], "failed")
        return _payment_result_page(
            "پرداخت ناموفق",
            "تأیید پرداخت انجام نشد. اشتراک فعال نشد و می‌توانید دوباره تلاش کنید.",
            ref_id=payment_id,
            page_class="failure",
            primary_label="رفتن به ربات",
        )

    gateway = create_zibal_gateway()
    verified, ref_id = await gateway.verify_payment(payment_id, transaction["amount"])
    if not verified:
        await transaction_service.update_transaction_status(transaction["id"], "failed")
        return _payment_result_page(
            "پرداخت ناموفق",
            "تأیید پرداخت انجام نشد. اشتراک فعال نشد و می‌توانید دوباره تلاش کنید.",
            ref_id=payment_id,
            page_class="failure",
            primary_label="رفتن به ربات",
        )

    subscription = await _activate_paid_subscription(
        transaction["user_id"], transaction["tier"], transaction["amount"]
    )
    await transaction_service.complete_transaction(transaction["id"], ref_id)
    await _notify_paid_user(
        transaction["user_id"],
        transaction["tier"],
        subscription.end_date,
        amount=transaction["amount"],
        ref_id=ref_id,
    )
    return _payment_result_page(
        "پرداخت تأیید شد",
        f"اشتراک {_tier_label(transaction['tier'])} فعال شد. حالا روبیفو آماده شروع کار است.",
        ref_id=ref_id,
        page_class="success",
    )


# ─────────────────────────────────────────────────────────────
# Admin HTML pages  /admin/<page>.html  and  /admin/
# ─────────────────────────────────────────────────────────────
@app.get("/admin/")
async def admin_root():
    return FileResponse(_STATIC_DIR / "login.html", media_type="text/html")


@app.get("/admin/{page}.html")
async def admin_page(page: str):
    fp = _STATIC_DIR / f"{page}.html"
    if fp.exists():
        return FileResponse(str(fp), media_type="text/html")
    return FileResponse(str(_STATIC_DIR / "login.html"), media_type="text/html")


# ─────────────────────────────────────────────────────────────
# Landing page  /
# ─────────────────────────────────────────────────────────────
@app.get("/795459943.txt", response_class=PlainTextResponse)
async def enamad_verification_file():
    return FileResponse(_ENAMAD_VERIFICATION_FILE, media_type="text/plain")


@app.get("/79545943.txt", response_class=PlainTextResponse)
async def enamad_legacy_verification_file():
    return FileResponse(_ENAMAD_LEGACY_VERIFICATION_FILE, media_type="text/plain")


@app.get("/")
async def landing():
    return FileResponse(_STATIC_DIR / "index.html", media_type="text/html")


# ─────────────────────────────────────────────────────────────
# Health check
# ─────────────────────────────────────────────────────────────
@app.get("/health")
async def health():
    return {"status": "ok"}


# ─────────────────────────────────────────────────────────────
# Bot webhook  POST /webhook
# ─────────────────────────────────────────────────────────────
_bot_ref = None


def _json_response(payload: dict, status_code: int = 200) -> JSONResponse:
    response = JSONResponse(payload, status_code=status_code)
    # Tests and older local helpers used `.status`; Starlette exposes `.status_code`.
    response.status = status_code
    return response


async def _register_inline_webhook_after_startup(client, webhook_url: str) -> None:
    """Register Rubika inline webhook after ASGI startup has returned.

    Rubika validates the URL during updateBotEndpoints. If this runs inside the
    FastAPI startup handler, Uvicorn has not started accepting requests yet and
    Rubika can reject an otherwise healthy URL as InvalidUrl.
    """
    from src.logger import logger

    await asyncio.sleep(5)
    try:
        await client.register_inline_webhook(webhook_url)
        logger.info(f"Inline webhook registered: {webhook_url}")
    except Exception as e:
        logger.error(f"Failed to register inline webhook; continuing with polling fallback: {e}")


async def _handle_webhook_payload(data: dict) -> JSONResponse:
    """Shared handler for all Rubika webhook payloads."""
    from src.logger import logger

    logger.info(f"[WEBHOOK] received keys={list(data.keys())} raw={str(data)[:200]}")

    # Webhook is registered as ReceiveInlineMessage — only process inline button presses.
    # NewMessage/StartedBot events arrive via polling and must not be double-processed here.
    if "inline_message" in data:
        msg = data.get("inline_message") or {}
        chat_id = msg.get("chat_id") or msg.get("sender_id")
        text = (msg.get("aux_data") or {}).get("button_id", "").strip()
        logger.info(f"[WEBHOOK] inline_message chat_id={chat_id} btn_id={text!r}")
        if not chat_id or not text:
            return _json_response({"ok": True})
        entry = {"user_id": str(chat_id), "text": text, "new_message": msg}
        client = _bot_ref.client if _bot_ref else None
        if client:
            from src.bot.handlers import route_message
            asyncio.create_task(route_message(client, str(chat_id), entry))
        else:
            logger.warning("[WEBHOOK] inline_message received but bot client not ready")
        return _json_response({"ok": True})

    # Any other event type (NewMessage, StartedBot, etc.) is handled by the polling loop.
    # Acknowledge receipt without processing to avoid duplicate message delivery.
    update_type = (data.get("update") or data).get("type", "")
    logger.info(f"[WEBHOOK] ignoring non-inline event type={update_type!r} (handled by polling)")
    return _json_response({"ok": True})


# Rubika validates the webhook endpoint with HEAD before sending events.
# We must respond 200 to HEAD on all webhook paths, otherwise Rubika
# considers the endpoint invalid and never delivers button click events.
@app.api_route("/webhook", methods=["GET", "HEAD"])
async def webhook_health(request: Request):
    return _json_response({"ok": True})


@app.api_route("/webhook/receiveInlineMessage", methods=["GET", "HEAD"])
async def webhook_inline_health(request: Request):
    return _json_response({"ok": True})


@app.api_route("/webhook/receiveUpdate", methods=["GET", "HEAD"])
async def webhook_update_health(request: Request):
    return _json_response({"ok": True})


# Rubika may POST to /webhook (base) OR /webhook/<type> depending on registration.
# We register the base URL and handle all paths here.
@app.post("/webhook")
async def webhook(request: Request):
    try:
        data = await request.json()
    except Exception:
        return _json_response({"ok": False}, status_code=400)
    return await _handle_webhook_payload(data)


@app.post("/webhook/receiveInlineMessage")
async def webhook_inline(request: Request):
    try:
        data = await request.json()
    except Exception:
        return _json_response({"ok": False}, status_code=400)
    # Normalize in case Rubika sends the payload unwrapped at this typed path
    if "inline_message" not in data and "update" not in data:
        data = {"inline_message": data}
    return await _handle_webhook_payload(data)


@app.post("/webhook/receiveUpdate")
async def webhook_update(request: Request):
    try:
        data = await request.json()
    except Exception:
        return _json_response({"ok": False}, status_code=400)
    return await _handle_webhook_payload(data)


@app.post("/webhook/receiveUpdate")
async def webhook_update(request: Request):
    try:
        data = await request.json()
    except Exception:
        return _json_response({"ok": False}, status_code=400)
    return await _handle_webhook_payload(data)


# ─────────────────────────────────────────────────────────────
# Startup / Shutdown
# ─────────────────────────────────────────────────────────────
@app.on_event("startup")
async def _startup():
    global _bot_ref
    from src.database import init_db
    from src.logger import logger
    import src.database as _db_mod

    await init_db()
    logger.info("Database pool ready")

    # Auto-apply missing migrations
    try:
        await _db_mod.pool.execute("""
            CREATE TABLE IF NOT EXISTS logs (
                id         SERIAL PRIMARY KEY,
                level      VARCHAR(20)  NOT NULL DEFAULT 'info',
                user_id    TEXT,
                action     VARCHAR(255),
                message    TEXT,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        await _db_mod.pool.execute(
            "CREATE INDEX IF NOT EXISTS idx_logs_user_id ON logs(user_id)"
        )
        await _db_mod.pool.execute(
            "CREATE INDEX IF NOT EXISTS idx_logs_level ON logs(level)"
        )
        await _db_mod.pool.execute(
            "CREATE INDEX IF NOT EXISTS idx_logs_created_at ON logs(created_at DESC)"
        )
        logger.info("Migration: logs table ensured")
    except Exception as e:
        logger.warning(f"Migration check failed: {e}")

    try:
        outbound_monitor = OutboundIPMonitor(_db_mod.pool)
        await outbound_monitor.ensure_table()
        if OUTBOUND_IP_CHECK_ENABLED:
            asyncio.create_task(outbound_monitor.run_forever())
            logger.info("Outbound IP monitor scheduled")
        else:
            logger.info("Outbound IP monitor disabled by config")
    except Exception as e:
        logger.warning(f"Outbound IP monitor startup failed: {e}")

    from src.config import BOT_TOKEN, RUBIKA_INLINE_WEBHOOK_URL
    from src.bot.main import RufifoBot, RubikaClient

    bot = RufifoBot(BOT_TOKEN)
    # Create and assign client NOW so webhook handler can use it immediately
    bot.client = RubikaClient(BOT_TOKEN)
    _bot_ref = bot

    if RUBIKA_INLINE_WEBHOOK_URL:
        asyncio.create_task(
            _register_inline_webhook_after_startup(bot.client, RUBIKA_INLINE_WEBHOOK_URL)
        )
        logger.info(f"Inline webhook registration scheduled: {RUBIKA_INLINE_WEBHOOK_URL}")

    asyncio.create_task(bot.start_webhook_mode())
    logger.info("Bot started (polling + inline webhook)")


@app.on_event("shutdown")
async def _shutdown():
    from src.database import close_db
    await close_db()


# ─────────────────────────────────────────────────────────────
# Direct run  (python app.py)
# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("app:app", host="0.0.0.0", port=port, log_level="info")


async def main():
    from src.config import RUBIKA_INLINE_WEBHOOK_URL

    if not RUBIKA_INLINE_WEBHOOK_URL:
        raise RuntimeError("RUBIKA_INLINE_WEBHOOK_URL is required for inline keyboard clicks")
    await _startup()
