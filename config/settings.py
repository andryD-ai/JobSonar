"""Application settings and configuration."""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from workspace root if present
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings:
    # Database
    DATA_DIR: Path = BASE_DIR / "data"
    DB_PATH: Path = DATA_DIR / "jobs.db"

    # Reports
    REPORTS_DIR: Path = BASE_DIR / "reports"

    # Browser automation / Facebook
    BROWSER_PROFILE_DIR: Path = DATA_DIR / "browser_profile"

    # LLM Settings
    DEFAULT_LLM_PROVIDER: str = os.getenv("DEFAULT_LLM_PROVIDER", "gemini").lower()
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")

    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3")

    # Network / Crawler settings
    REQUEST_TIMEOUT: int = int(os.getenv("REQUEST_TIMEOUT", "25"))
    USER_AGENT: str = os.getenv(
        "USER_AGENT",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
    )

    def init_directories(self) -> None:
        """Ensure all required runtime directories exist."""
        self.DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        self.BROWSER_PROFILE_DIR.mkdir(parents=True, exist_ok=True)

settings = Settings()
settings.init_directories()
