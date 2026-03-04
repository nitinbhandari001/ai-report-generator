from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import structlog
from dotenv import load_dotenv

load_dotenv()

_BASE = Path(__file__).parent.parent


@dataclass(frozen=True)
class Settings:
    # AI providers
    groq_api_key: str = ""
    gemini_api_key: str = ""
    openrouter_api_key: str = ""

    # Database (optional)
    database_url: str = ""

    # Storage
    reports_dir: Path = _BASE / "data" / "reports"
    uploads_dir: Path = _BASE / "data" / "uploads"

    # Limits
    max_upload_mb: int = 50
    max_charts: int = 6

    # Report defaults
    default_page_size: str = "A4"
    default_palette: str = "professional"

    # Server
    fastapi_port: int = 8004
    log_level: str = "INFO"

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            groq_api_key=os.getenv("GROQ_API_KEY", ""),
            gemini_api_key=os.getenv("GEMINI_API_KEY", ""),
            openrouter_api_key=os.getenv("OPENROUTER_API_KEY", ""),
            database_url=os.getenv("DATABASE_URL", ""),
            reports_dir=Path(os.getenv("REPORTS_DIR", str(_BASE / "data" / "reports"))),
            uploads_dir=Path(os.getenv("UPLOADS_DIR", str(_BASE / "data" / "uploads"))),
            max_upload_mb=int(os.getenv("MAX_UPLOAD_MB", "50")),
            max_charts=int(os.getenv("MAX_CHARTS", "6")),
            default_page_size=os.getenv("DEFAULT_PAGE_SIZE", "A4"),
            default_palette=os.getenv("DEFAULT_PALETTE", "professional"),
            fastapi_port=int(os.getenv("FASTAPI_PORT", "8004")),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings.from_env()


def configure_logging(level: str = "INFO") -> None:
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(__import__("logging"), level, 20)
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
    )
