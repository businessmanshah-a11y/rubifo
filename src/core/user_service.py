from typing import Optional
from datetime import datetime, timedelta
import re
import bcrypt
from src.models.user import User
from src.config import TRIAL_DURATION_HOURS
from src.logger import logger
from src.utils import now_tehran


class UserService:
    """Service for user management and operations."""

    def __init__(self, db):
        self.db = db

    @staticmethod
    def normalize_phone(phone_number: str) -> str:
        """Normalize and validate an Iranian mobile phone number."""
        from src.utils import normalize_digits

        normalized = normalize_digits((phone_number or "").strip()).replace(" ", "")
        normalized = normalized.replace("-", "")
        if not re.fullmatch(r"09\d{9}", normalized):
            raise ValueError("phone_number must be an Iranian mobile number like 09123456789")
        return normalized

    @staticmethod
    def hash_password(password: str) -> str:
        if len(password or "") < 6:
            raise ValueError("password must be at least 6 characters")
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        try:
            return bcrypt.checkpw(
                (password or "").encode("utf-8"), (password_hash or "").encode("utf-8")
            )
        except Exception:
            return False

    async def get_or_create_user(
        self, user_id: str, username: Optional[str] = None
    ) -> User:
        """Get existing user or create new one with trial.

        Args:
            user_id: Rubika user ID
            username: Optional username

        Returns:
            User instance
        """
        result = await self.db.fetchrow("SELECT * FROM users WHERE user_id = $1", user_id)

        if result:
            logger.info(f"User {user_id} found in database")
            return User(**result)

        logger.info(f"Creating new user {user_id} with trial")
        trial_end = now_tehran() + timedelta(hours=TRIAL_DURATION_HOURS)

        await self.db.execute(
            "INSERT INTO users (user_id, username, trial_end_at) VALUES ($1, $2, $3) "
            "ON CONFLICT (user_id) DO NOTHING",
            user_id,
            username,
            trial_end,
        )

        return await self.get_user(user_id)

    async def get_user(self, user_id: str) -> Optional[User]:
        """Fetch user by user_id.

        Args:
            user_id: Rubika user ID

        Returns:
            User instance or None if not found
        """
        if isinstance(user_id, int) and user_id < 0:
            raise ValueError("user_id must be positive")
        result = await self.db.fetchrow("SELECT * FROM users WHERE user_id = $1", user_id)
        return User(**dict(result)) if result else None

    async def set_web_credentials(
        self, user_id: str, phone_number: str, password: str
    ) -> User:
        """Store website login credentials for a Rubika user."""
        normalized_phone = self.normalize_phone(phone_number)
        password_hash = self.hash_password(password)

        result = await self.db.fetchrow(
            """
            UPDATE users
            SET phone_number = $1,
                password_hash = $2,
                onboarding_completed_at = NOW(),
                updated_at = NOW()
            WHERE user_id = $3
            RETURNING *
            """,
            normalized_phone,
            password_hash,
            user_id,
        )
        if result:
            return User(**dict(result))

        await self.db.execute(
            """
            UPDATE users
            SET phone_number = $1,
                password_hash = $2,
                onboarding_completed_at = NOW(),
                updated_at = NOW()
            WHERE user_id = $3
            """,
            normalized_phone,
            password_hash,
            user_id,
        )
        user = await self.get_user(user_id)
        return user or User(user_id=user_id, phone_number=normalized_phone, password_hash=password_hash)

    async def update_web_phone(self, user_id: str, phone_number: str) -> User:
        """Update only the website login phone number for a Rubika user."""
        normalized_phone = self.normalize_phone(phone_number)
        result = await self.db.fetchrow(
            """
            UPDATE users
            SET phone_number = $1,
                onboarding_completed_at = COALESCE(onboarding_completed_at, NOW()),
                updated_at = NOW()
            WHERE user_id = $2
            RETURNING *
            """,
            normalized_phone,
            user_id,
        )
        if result:
            return User(**dict(result))

        await self.db.execute(
            """
            UPDATE users
            SET phone_number = $1,
                onboarding_completed_at = COALESCE(onboarding_completed_at, NOW()),
                updated_at = NOW()
            WHERE user_id = $2
            """,
            normalized_phone,
            user_id,
        )
        user = await self.get_user(user_id)
        return user or User(user_id=user_id, phone_number=normalized_phone)

    async def update_web_password(self, user_id: str, password: str) -> User:
        """Update only the website login password hash for a Rubika user."""
        password_hash = self.hash_password(password)
        result = await self.db.fetchrow(
            """
            UPDATE users
            SET password_hash = $1,
                onboarding_completed_at = COALESCE(onboarding_completed_at, NOW()),
                updated_at = NOW()
            WHERE user_id = $2
            RETURNING *
            """,
            password_hash,
            user_id,
        )
        if result:
            return User(**dict(result))

        await self.db.execute(
            """
            UPDATE users
            SET password_hash = $1,
                onboarding_completed_at = COALESCE(onboarding_completed_at, NOW()),
                updated_at = NOW()
            WHERE user_id = $2
            """,
            password_hash,
            user_id,
        )
        user = await self.get_user(user_id)
        return user or User(user_id=user_id, password_hash=password_hash)

    async def get_user_by_phone(self, phone_number: str) -> Optional[User]:
        normalized_phone = self.normalize_phone(phone_number)
        result = await self.db.fetchrow(
            "SELECT * FROM users WHERE phone_number = $1", normalized_phone
        )
        return User(**dict(result)) if result else None

    async def authenticate_web_user(
        self, phone_number: str, password: str
    ) -> Optional[User]:
        user = await self.get_user_by_phone(phone_number)
        if not user or not user.password_hash:
            return None
        if not self.verify_password(password, user.password_hash):
            return None
        return user

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
        self, web_user_id: str, rubika_guid: str, trial_hours: int = None
    ) -> User:
        """Merge a web-registered user into an existing bot user.

        Transfers all FK data (subscriptions, transactions, logs) from the
        web placeholder user to the rubika_guid user, then deletes the placeholder.
        Trial starts on the rubika_guid user upon merge.
        JWT tokens for web_user_id become invalid after this call.
        """
        if trial_hours is None:
            trial_hours = TRIAL_DURATION_HOURS
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
                        trial_end_at         = NOW() + ($4 * INTERVAL '1 hour'),
                        updated_at           = NOW()
                    WHERE user_id = $3
                    RETURNING *
                    """,
                    web_user.phone_number,
                    web_user.password_hash,
                    rubika_guid,
                    trial_hours,
                )

        merged = User(**dict(result))
        logger.info(f"Merged web account {web_user_id} → bot user {rubika_guid}")
        return merged

    async def list_users(self, limit: int = 100, offset: int = 0):
        """List users with pagination.

        Args:
            limit: Number of users to return
            offset: Offset for pagination

        Returns:
            List of User instances
        """
        results = await self.db.fetch(
            "SELECT * FROM users ORDER BY created_at DESC LIMIT $1 OFFSET $2",
            limit,
            offset,
        )
        return [User(**dict(row)) for row in results]

    async def check_trial_expiration(self, user_id: str) -> bool:
        """Check if trial has expired and disable routes if needed.

        Args:
            user_id: Rubika user ID

        Returns:
            True if trial expired, False otherwise
        """
        user = await self.get_user(user_id)

        if not user:
            return False

        if user.is_trial_active and now_tehran() > user.trial_end_at:
            logger.info(f"Trial expired for user {user_id}, disabling routes")

            await self.db.execute(
                "UPDATE routes SET is_active = false WHERE user_id = $1", user_id
            )

            await self.db.execute(
                "UPDATE users SET is_trial_active = false WHERE user_id = $1", user_id
            )

            return True

        return False

    async def update_trial_end(self, user_id: str, hours: int) -> None:
        """Update trial end date for a user.

        Args:
            user_id: Rubika user ID
            hours: Number of hours to extend trial by
        """
        new_end = now_tehran() + timedelta(hours=hours)
        await self.db.execute(
            "UPDATE users SET trial_end_at = $1, is_trial_active = true "
            "WHERE user_id = $2",
            new_end,
            user_id,
        )
        logger.info(f"Trial extended for user {user_id} by {hours} hours")

    async def update_trial_status(self, user_id: str, is_active: bool) -> None:
        """Update trial active flag for a user."""
        await self.db.execute(
            "UPDATE users SET is_trial_active = $1 WHERE user_id = $2",
            is_active,
            user_id,
        )
        logger.info(f"Trial status updated for user {user_id}: {is_active}")
