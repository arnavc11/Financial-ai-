import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    COINGECKO_BASE_URL: str = "https://api.coingecko.com/api/v3"
    
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = "llama-3.3-70b-versatile"  
    
    GNEWS_API_KEY: str = os.getenv("GNEWS_API_KEY", "")
    GNEWS_BASE_URL: str = "https://gnews.io/api/v4"
    
    ALPHA_VANTAGE_API_KEY: str = os.getenv("ALPHA_VANTAGE_API_KEY", "demo")
    USE_YFINANCE_FALLBACK: bool = True
    DATA_DIR: str = "data"

config = Config()
