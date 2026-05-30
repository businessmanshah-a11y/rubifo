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
from pathlib import Path
from pydantic import BaseModel
from jose import JWTError, jwt
from fastapi import FastAPI, Depends, HTTPException, Request, status
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.staticfiles import StaticFiles
import src.database as db_module
from src.config import (
    RUBIKA_BOT_RETURN_URL,
    SUBSCRIPTION_TIERS,
    USER_JWT_SECRET,
    WEB_BASE_URL,
)
from src.core.subscription_service import SubscriptionService
from src.core.transaction_service import TransactionService
from src.core.user_service import UserService
from src.integrations.zarinpal import create_zarinpal_gateway
from src.utils import to_jalali_date

_STATIC_DIR = Path(__file__).parent / "src" / "admin" / "static"

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


class _CheckoutStartBody(BaseModel):
    tier: str


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


def _create_user_token(user_id: str) -> str:
    from datetime import datetime, timedelta

    payload = {
        "scope": "web_user",
        "sub": user_id,
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


def _html_page(title: str, body: str) -> HTMLResponse:
    return HTMLResponse(
        f"""<!doctype html>
<html lang="fa" dir="rtl">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  <link rel="stylesheet" href="/static/css/style.css">
</head>
<body>
  <main class="container" style="max-width:760px;margin:40px auto;padding:24px;">
    {body}
  </main>
</body>
</html>"""
    )


@app.get("/login")
async def web_login_page(next: str = "/checkout", tier: str = ""):
    action_hint = f"{next}?tier={tier}" if tier else next
    return _html_page(
        "ورود به Rubifo",
        f"""
        <h1>ورود به Rubifo</h1>
        <p>با شماره تماس و رمزی که داخل ربات ثبت کرده‌اید وارد شوید.</p>
        <form id="login-form">
          <label>شماره تماس</label>
          <input name="phone_number" autocomplete="tel" placeholder="09123456789" required>
          <label>رمز عبور</label>
          <input name="password" type="password" autocomplete="current-password" required>
          <button type="submit">ورود</button>
        </form>
        <p id="login-error" style="color:#b00020;"></p>
        <script>
        document.getElementById('login-form').addEventListener('submit', async (event) => {{
          event.preventDefault();
          const form = new FormData(event.currentTarget);
          const res = await fetch('/api/auth/login', {{
            method: 'POST',
            headers: {{'Content-Type': 'application/json'}},
            body: JSON.stringify({{
              phone_number: form.get('phone_number'),
              password: form.get('password')
            }})
          }});
          if (!res.ok) {{
            document.getElementById('login-error').textContent = 'شماره تماس یا رمز عبور اشتباه است.';
            return;
          }}
          const data = await res.json();
          localStorage.setItem('rubifo_user_token', data.access_token);
          window.location.href = {action_hint!r};
        }});
        </script>
        """,
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
            detail="شماره تماس یا رمز عبور اشتباه است",
        )

    return {
        "access_token": _create_user_token(user.user_id),
        "token_type": "bearer",
        "user": {
            "user_id": user.user_id,
            "username": user.username,
            "phone_number": user.phone_number,
        },
    }


@app.get("/checkout")
async def checkout_page(tier: str = "basic"):
    if tier not in SUBSCRIPTION_TIERS:
        return _html_page(
            "پلن نامعتبر",
            "<h1>پلن نامعتبر است</h1><p>لطفاً از داخل ربات دوباره گزینه خرید را انتخاب کنید.</p>",
        )

    options = "\n".join(
        f"<option value='{key}' {'selected' if key == tier else ''}>"
        f"{cfg['display_name_fa']} - {cfg['price_monthly']:,} تومان</option>"
        for key, cfg in SUBSCRIPTION_TIERS.items()
    )
    return _html_page(
        "خرید اشتراک Rubifo",
        f"""
        <h1>خرید اشتراک Rubifo</h1>
        <p>پلن را انتخاب کنید و پرداخت را در زرین‌پال ادامه دهید.</p>
        <label>پلن</label>
        <select id="tier">{options}</select>
        <button id="pay">پرداخت</button>
        <p id="checkout-error" style="color:#b00020;"></p>
        <script>
        document.getElementById('pay').addEventListener('click', async () => {{
          const token = localStorage.getItem('rubifo_user_token');
          if (!token) {{
            window.location.href = '/login?next=/checkout&tier=' + encodeURIComponent(document.getElementById('tier').value);
            return;
          }}
          const res = await fetch('/api/checkout/start', {{
            method: 'POST',
            headers: {{
              'Content-Type': 'application/json',
              'Authorization': 'Bearer ' + token
            }},
            body: JSON.stringify({{tier: document.getElementById('tier').value}})
          }});
          if (res.status === 401) {{
            window.location.href = '/login?next=/checkout&tier=' + encodeURIComponent(document.getElementById('tier').value);
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
    )


@app.post("/api/checkout/start")
async def checkout_start(body: _CheckoutStartBody, user=Depends(_current_web_user)):
    if body.tier not in SUBSCRIPTION_TIERS:
        raise HTTPException(status_code=400, detail="Invalid subscription tier")

    tier_config = SUBSCRIPTION_TIERS[body.tier]
    amount = tier_config["price_monthly"]
    callback_url = f"{WEB_BASE_URL.rstrip('/')}/payment/callback"
    gateway = create_zarinpal_gateway(sandbox=True)
    success, result = await gateway.request_payment(
        amount=amount,
        description=f"اشتراک {tier_config['display_name_fa']} - Rubifo",
        callback_url=callback_url,
    )
    if not success:
        raise HTTPException(status_code=502, detail=result)

    authority = result.split("/StartPay/")[-1]
    await TransactionService(_web_db()).create_pending_transaction(
        user.user_id, amount, body.tier, authority
    )
    return {"payment_url": result, "authority": authority}


def _payment_result_page(title: str, message: str) -> HTMLResponse:
    return _html_page(
        title,
        f"""
        <h1>{title}</h1>
        <p>{message}</p>
        <a href="{RUBIKA_BOT_RETURN_URL}">بازگشت به ربات</a>
        """,
    )


async def _notify_paid_user(user_id: str, tier: str, end_date) -> None:
    client = _bot_ref.client if _bot_ref else None
    if not client:
        return
    try:
        await client.send_message(
            user_id,
            f"✅ پرداخت تأیید شد!\n\n"
            f"اشتراک {SUBSCRIPTION_TIERS[tier]['display_name_fa']} فعال شد.\n"
            f"تاریخ پایان: {to_jalali_date(end_date)}"
        )
    except Exception:
        pass


@app.get("/payment/callback")
async def payment_callback(Authority: str = "", Status: str = ""):
    if not Authority:
        return _payment_result_page("پرداخت نامعتبر", "شناسه پرداخت از زرین‌پال دریافت نشد.")

    transaction_service = TransactionService(_web_db())
    transaction = await transaction_service.get_transaction_by_authority(Authority)
    if not transaction:
        return _payment_result_page("پرداخت پیدا نشد", "این پرداخت در Rubifo ثبت نشده است.")

    if transaction.get("status") == "completed":
        ref = transaction.get("reference_id") or "ثبت‌شده"
        return _payment_result_page("پرداخت قبلاً تأیید شده", f"کد رهگیری: {ref}")

    if Status and Status.upper() != "OK":
        await transaction_service.update_transaction_status(transaction["id"], "canceled")
        return _payment_result_page("پرداخت لغو شد", "پرداخت از سمت درگاه لغو شد.")

    gateway = create_zarinpal_gateway(sandbox=True)
    success, ref_id = await gateway.verify_payment(Authority, transaction["amount"])
    if not success:
        await transaction_service.update_transaction_status(transaction["id"], "failed")
        return _payment_result_page("پرداخت ناموفق", "تأیید پرداخت انجام نشد. لطفاً دوباره تلاش کنید.")

    subscription = await SubscriptionService(_web_db()).create_subscription(
        transaction["user_id"], transaction["tier"], days=30
    )
    await transaction_service.complete_transaction(transaction["id"], ref_id)
    await _notify_paid_user(transaction["user_id"], transaction["tier"], subscription.end_date)
    return _payment_result_page(
        "پرداخت تأیید شد",
        f"اشتراک شما فعال شد. کد رهگیری: {ref_id}",
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

    raw = data.get("update") or data
    update_type = raw.get("type", "")
    chat_id = raw.get("chat_id")

    if not chat_id:
        return _json_response({"ok": True})

    if update_type == "NewMessage":
        msg = raw.get("new_message") or {}
        text = (msg.get("text") or "").strip()
        if not text:
            btn_id = (msg.get("aux_data") or {}).get("button_id", "")
            if btn_id:
                text = f"/{btn_id}"
        entry = {"user_id": str(chat_id), "text": text, "new_message": msg}
        fwd = msg.get("forwarded_from") or {}
        if fwd:
            entry["forwarded_from_chat"] = str(
                fwd.get("from_chat_id") or fwd.get("chat_id") or fwd.get("object_guid", "")
            )
            entry["forwarded_message_id"] = str(msg.get("message_id", ""))
    elif update_type == "StartedBot":
        entry = {"user_id": str(chat_id), "text": "/start", "new_message": {}}
    else:
        return _json_response({"ok": True})

    if _bot_ref and _bot_ref.client:
        from src.bot.handlers import route_message
        asyncio.create_task(route_message(_bot_ref.client, str(chat_id), entry))

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
