import os
from dotenv import load_dotenv

load_dotenv()

# Bot Configuration
BOT_TOKEN = os.getenv("BOT_TOKEN")
BOT_NAME = "rubifo"
TIMEZONE = os.getenv("TIMEZONE", "Asia/Tehran")

# Database
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/rubifo")

# Payment Gateway
ZARINPAL_MERCHANT_ID = os.getenv("ZARINPAL_MERCHANT_ID")

# Admin Panel
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD_HASH = os.getenv("ADMIN_PASSWORD_HASH")
JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-change-in-production")

# Logging
LOG_FILE = os.getenv("LOG_FILE", "rubifo.log")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Trial Configuration
TRIAL_DURATION_HOURS = int(os.getenv("TRIAL_DURATION_HOURS", "48"))
TRIAL_REMINDER_HOURS = int(os.getenv("TRIAL_REMINDER_HOURS", "24"))

# Rubika User Session (for reading channel posts)
USER_SESSION_NAME = os.getenv("USER_SESSION_NAME", "rubifo_user")
CHANNEL_POLL_INTERVAL = int(os.getenv("CHANNEL_POLL_INTERVAL", "60"))  # seconds between polls

# API Rate Limiting
API_RATE_LIMIT_DELAY = float(os.getenv("API_RATE_LIMIT_DELAY", "0.5"))

# Schedule Check
SCHEDULE_CHECK_INTERVAL = int(os.getenv("SCHEDULE_CHECK_INTERVAL", "30"))

# Subscription Tiers
SUBSCRIPTION_TIERS = {
    "basic": {"max_routes": 1, "price_monthly": 50000},
    "pro": {"max_routes": 3, "price_monthly": 120000},
    "enterprise": {"max_routes": 10, "price_monthly": 350000},
}
