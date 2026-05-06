import os
from dotenv import load_dotenv

load_dotenv()

class Config:

    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    CLAUDE_MODEL: str = "claude-sonnet-4-20250514"

    ALPHA_VANTAGE_API_KEY: str = os.getenv("ALPHA_VANTAGE_API_KEY", "demo")

    USE_YFINANCE_FALLBACK: bool = True

    COINGECKO_BASE_URL: str = "https://api.coingecko.com/api/v3"
    COINGECKO_API_KEY: str = os.getenv("COINGECKO_API_KEY", "")

    MFAPI_BASE_URL: str = "https://api.mfapi.in/mf"

    RBI_DBIE_BASE_URL: str = "https://api.rbi.org.in/api/v1"

    NEWS_API_KEY: str = os.getenv("NEWS_API_KEY", "")
    NEWS_API_BASE_URL: str = "https://newsapi.org/v2"

    SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASS: str = os.getenv("SMTP_PASS", "")

    DATA_DIR: str = "data"
    ALERT_CHECK_INTERVAL_SECONDS: int = 60
    DATA_REFRESH_INTERVAL_SECONDS: int = 300

config = Config()
