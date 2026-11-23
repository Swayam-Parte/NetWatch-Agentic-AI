"""Central settings for NetWatch 2.0."""
from dataclasses import dataclass
import os
from dotenv import load_dotenv
load_dotenv()

@dataclass(frozen=True)
class Settings:
    app_name: str = "NetWatch"
    app_version: str = "2.0.0-m5"
    max_troubleshooting_attempts: int = int(os.getenv("MAX_TROUBLESHOOTING_ATTEMPTS", "3"))
    memory_similarity_threshold: float = float(os.getenv("MEMORY_SIMILARITY_THRESHOLD", "0.08"))
    database_path: str = os.getenv("DATABASE_PATH", "data/netwatch.db")
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
settings = Settings()
