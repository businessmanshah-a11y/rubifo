from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthCredentials
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from src.admin.auth import AdminAuth
from src.logger import logger

app = FastAPI(title="Rubifo Admin")

# Serve static files
static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Import and include routers
from src.admin import routes
app.include_router(routes.router)
security = HTTPBearer()
auth = AdminAuth()


async def verify_token(credentials: HTTPAuthCredentials = Depends(security)) -> str:
    """Dependency to verify JWT token and return username.

    Args:
        credentials: HTTP Bearer credentials

    Returns:
        Username if token is valid

    Raises:
        HTTPException if token is invalid
    """
    token = credentials.credentials
    username = auth.verify_token(token)

    if not username:
        logger.warning("Invalid token attempted")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )

    return username


@app.get("/")
async def root():
    """Redirect to login page."""
    from fastapi.responses import FileResponse
    return FileResponse(static_dir / "login.html", media_type="text/html")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}


@app.post("/admin/login")
async def login(username: str, password: str):
    """Authenticate admin and return JWT token.

    Args:
        username: Admin username
        password: Admin password

    Returns:
        JWT token if valid

    Raises:
        HTTPException if credentials invalid
    """
    token = auth.authenticate(username, password)

    if not token:
        logger.warning(f"Failed login attempt for {username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )

    return {"access_token": token, "token_type": "bearer"}


@app.get("/admin/dashboard")
async def get_dashboard(username: str = Depends(verify_token)):
    """Protected dashboard endpoint.

    Args:
        username: Authenticated username

    Returns:
        Dashboard data
    """
    logger.info(f"Dashboard accessed by {username}")
    return {"message": "Dashboard data coming soon"}
