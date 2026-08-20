"""
Application configuration using pydantic-settings.
Loads from environment variables / .env file.
"""

from pydantic_settings import BaseSettings
from typing import List
from pathlib import Path


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://bingo_user:bingo_password@db:5432/code_bingo"

    # JWT
    SECRET_KEY: str = "your-super-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480

    # App
    BACKEND_URL: str = "http://localhost:8000"
    FRONTEND_URL: str = "http://localhost:5173"
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000"

    # Admin defaults
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "admin123"
    ADMIN_EMAIL: str = "admin@codebingo.com"

    # Firebase (web API key for token verification)
    FIREBASE_API_KEY: str = "AIzaSyDLppUdeGbuYK5oM82bSTo-6DwYQEWkz1k"

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    class Config:
        env_file = Path(__file__).resolve().parents[2] / ".env"
        case_sensitive = True
        extra = "ignore"


settings = Settings()
