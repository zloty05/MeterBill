"""Konfiguracja aplikacji ładowana ze zmiennych środowiskowych (.env)."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Supabase
    supabase_url: str = ""
    supabase_service_key: str = ""
    supabase_anon_key: str = ""
    supabase_jwt_secret: str = ""

    # Redis (Celery)
    redis_url: str = "redis://redis:6379/0"

    # Email (Resend)
    resend_api_key: str = ""
    from_email: str = ""

    # App
    secret_key: str = "change-me"
    environment: str = "development"
    base_url: str = "http://localhost:8000"
    frontend_url: str = "http://localhost:3000"

    # Faktury / scheduler
    invoice_generation_day: int = 1
    invoice_due_days: int = 14
    portal_token_ttl_days: int = 90


@lru_cache
def get_settings() -> Settings:
    return Settings()
