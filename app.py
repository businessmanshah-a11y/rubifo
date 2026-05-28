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
from fastapi import FastAPI, Depends, HTTPException, Request, status
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

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


@app.post("/admin/login")
async def admin_login(body: _LoginBody):
    token = auth_service.authenticate(body.username, body.password)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="نام کاربری یا رمز عبور اشتباه است")
    return {"access_token": token, "token_type": "bearer"}


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


@app.post("/webhook")
async def webhook(request: Request):
    try:
        data = await request.json()
    except Exception:
        return JSONResponse({"ok": False}, status_code=400)

    raw = data.get("update") or data
    update_type = raw.get("type", "")
    chat_id = raw.get("chat_id")

    if not chat_id:
        return JSONResponse({"ok": True})

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
            entry["forwarded_from_chat"] = str(fwd.get("chat_id") or fwd.get("object_guid", ""))
            entry["forwarded_message_id"] = str(msg.get("message_id", ""))
    elif update_type == "StartedBot":
        entry = {"user_id": str(chat_id), "text": "/start", "new_message": {}}
    else:
        return JSONResponse({"ok": True})

    if _bot_ref and _bot_ref.client:
        from src.bot.handlers import route_message
        asyncio.create_task(route_message(_bot_ref.client, str(chat_id), entry))

    return JSONResponse({"ok": True})


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

    from src.config import BOT_TOKEN
    from src.bot.main import RufifoBot

    bot = RufifoBot(BOT_TOKEN)
    _bot_ref = bot
    # Webhook mode: messages arrive via POST /webhook — no polling loop
    asyncio.create_task(bot.start_webhook_mode())
    logger.info("Bot started in webhook mode (no polling)")


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
