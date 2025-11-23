import os
from dotenv import load_dotenv
from typing import List

load_dotenv()

API_VERSION = "1.0.0"

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
SERPAPI_KEY = os.getenv("SERPAPI_KEY")

DEFAULT_ENTITY = os.getenv("DEFAULT_ENTITY", "Taboola")
DEFAULT_DAYS = int(os.getenv("DEFAULT_DAYS", "30"))
DEFAULT_LIMIT = int(os.getenv("DEFAULT_LIMIT", "20"))

CORS_ORIGINS: List[str] = [o.strip() for o in os.getenv("CORS_ORIGINS", "*").split(",") if o.strip()]
CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", "300"))  # 5 minutes
RATE_LIMIT_QPS = float(os.getenv("RATE_LIMIT_QPS", "10"))
