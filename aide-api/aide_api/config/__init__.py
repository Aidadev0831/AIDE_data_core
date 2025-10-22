"""Configuration for AIDE API"""

import os
from typing import List
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    """API Settings"""

    # Database
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./aide_dev.db")

    # API Info
    api_title: str = os.getenv("API_TITLE", "AIDE API")
    api_version: str = os.getenv("API_VERSION", "0.1.0")
    api_description: str = os.getenv(
        "API_DESCRIPTION",
        "REST API for AIDE Platform - News, Policies, and Ratings"
    )

    # Server
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8000"))
    reload: bool = os.getenv("RELOAD", "false").lower() == "true"

    # CORS
    cors_origins: List[str] = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:3000,http://localhost:8000"
    ).split(",")
    cors_allow_credentials: bool = os.getenv("CORS_ALLOW_CREDENTIALS", "true").lower() == "true"

    # Pagination
    default_page_size: int = int(os.getenv("DEFAULT_PAGE_SIZE", "20"))
    max_page_size: int = int(os.getenv("MAX_PAGE_SIZE", "100"))

    class Config:
        env_file = ".env"


settings = Settings()
