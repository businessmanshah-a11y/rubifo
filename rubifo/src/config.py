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
TRIAL_DURATION_HOURS = int(os.getenv("TRIAL_DURATION_HOURS", "72"))
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
    "basic": {
        "display_name_fa": "شروع حرفه‌ای",
        "max_destinations": 1,
        "price_monthly": 1998000,
    },
    "pro": {
        "display_name_fa": "رشد",
        "max_destinations": 3,
        "price_monthly": 3998000,
    },
    "enterprise": {
        "display_name_fa": "مقیاس",
        "max_destinations": 10,
        "price_monthly": 9998000,
    },
}
