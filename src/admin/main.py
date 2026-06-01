from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.responses import FileResponse, PlainTextResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from pathlib import Path
from src.admin.auth import verify_token, auth_service
from src.logger import logger

app = FastAPI(title="Rubifo Admin")


@app.on_event("startup")
async def startup_event():
    """Initialize database connection pool on startup."""
    from src.database import init_db
    await init_db()
    logger.info("Admin panel database pool initialized")


@app.on_event("shutdown")
async def shutdown_event():
    """Close database connection pool on shutdown."""
    from src.database import close_db
    await close_db()


# Serve static files
static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Import and include routers
from src.admin import routes
app.include_router(routes.router)


@app.get("/admin/{page}.html")
async def serve_html_page(page: str):
    """Serve admin HTML pages."""
    file_path = static_dir / f"{page}.html"
    if file_path.exists():
        return FileResponse(str(file_path), media_type="text/html")
    return FileResponse(str(static_dir / "login.html"), media_type="text/html")


@app.get("/")
async def root():
    return FileResponse(static_dir / "index.html", media_type="text/html")


@app.get("/795459943.txt", response_class=PlainTextResponse)
async def enamad_verification_file():
    return ""


@app.get("/admin/")
async def admin_root():
    return FileResponse(static_dir / "login.html", media_type="text/html")


@app.get("/health")
async def health_check():
    return {"status": "ok"}


class LoginRequest(BaseModel):
    username: str
    password: str


@app.post("/admin/login")
async def login(body: LoginRequest):
    """Authenticate admin and return JWT token."""
    token = auth_service.authenticate(body.username, body.password)

    if not token:
        logger.warning(f"Failed login attempt for {body.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )

    return {"access_token": token, "token_type": "bearer"}


@app.get("/admin/dashboard")
async def get_dashboard(username: str = Depends(verify_token)):
    logger.info(f"Dashboard accessed by {username}")
    return {"message": "Dashboard data coming soon"}
