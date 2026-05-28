import bcrypt
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer
from src.config import ADMIN_USERNAME, ADMIN_PASSWORD_HASH, JWT_SECRET
from src.logger import logger


class AdminAuth:
    """Authentication manager for admin dashboard."""

    def __init__(
        self,
        secret_key: str = JWT_SECRET,
        admin_username: str = ADMIN_USERNAME,
        admin_password_hash: str = ADMIN_PASSWORD_HASH,
        token_expiry_hours: int = 24,
    ):
        self.secret_key = secret_key
        self.admin_username = admin_username
        self.admin_password_hash = admin_password_hash
        self.token_expiry_hours = token_expiry_hours
        self.algorithm = "HS256"

    def verify_password(self, password: str) -> bool:
        """Verify password against bcrypt hash.

        Args:
            password: Plain text password to verify

        Returns:
            True if password matches, False otherwise
        """
        try:
            return bcrypt.checkpw(
                password.encode("utf-8"), self.admin_password_hash.encode("utf-8")
            )
        except Exception as e:
            logger.error(f"Password verification error: {e}")
            return False

    def create_token(self, username: str) -> str:
        """Create JWT token for authenticated user.

        Args:
            username: Username to encode in token

        Returns:
            JWT token string
        """
        payload = {
            "username": username,
            "exp": datetime.utcnow() + timedelta(hours=self.token_expiry_hours),
            "iat": datetime.utcnow(),
        }

        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        logger.info(f"Token created for user {username}")

        return token

    def verify_token(self, token: str) -> Optional[str]:
        """Verify JWT token and return username.

        Args:
            token: JWT token string

        Returns:
            Username if token is valid, None otherwise
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            username = payload.get("username")

            if username:
                logger.info(f"Token verified for user {username}")
                return username

        except JWTError as e:
            logger.warning(f"Token verification failed: {e}")

        return None

    def authenticate(self, username: str, password: str) -> Optional[str]:
        """Authenticate user and return token if valid.

        Args:
            username: Username
            password: Plain text password

        Returns:
            JWT token if valid, None otherwise
        """
        if username != self.admin_username:
            logger.warning(f"Login attempt with wrong username: {username}")
            return None

        if not self.verify_password(password):
            logger.warning(f"Login attempt with wrong password for {username}")
            return None

        logger.info(f"User {username} authenticated successfully")
        return self.create_token(username)


# FastAPI dependency for token verification
security = HTTPBearer()
auth_service = AdminAuth()


async def verify_token(credentials = Depends(security)) -> str:
    """Dependency to verify JWT token and return username.

    Args:
        credentials: HTTP Bearer credentials

    Returns:
        Username if token is valid

    Raises:
        HTTPException if token is invalid
    """
    token = credentials.credentials
    username = auth_service.verify_token(token)

    if not username:
        logger.warning("Invalid token attempted")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )

    return username
