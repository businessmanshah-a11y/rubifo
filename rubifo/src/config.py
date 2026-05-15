import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/rubifo")
ZARINPAL_MERCHANT_ID = os.getenv("ZARINPAL_MERCHANT_ID")
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD_HASH = os.getenv("ADMIN_PASSWORD_HASH")

# Bot configuration
BOT_NAME = "rubifo"
API_RATE_LIMIT_DELAY = 0.5  # seconds between API calls
SCHEDULE_CHECK_INTERVAL = 30  # seconds

# Trial configuration
TRIAL_DURATION_HOURS = 48
TRIAL_REMINDER_HOURS = 24
