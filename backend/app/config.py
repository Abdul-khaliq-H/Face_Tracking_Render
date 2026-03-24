from urllib.parse import urlparse, urlunparse

from pydantic_settings import BaseSettings, SettingsConfigDict


def normalize_database_url(database_url: str) -> str:
    if not database_url:
        return database_url

    parsed = urlparse(database_url)

    if parsed.scheme == "postgres":
        return urlunparse(parsed._replace(scheme="postgresql+psycopg"))

    if parsed.scheme == "postgresql":
        return urlunparse(parsed._replace(scheme="postgresql+psycopg"))

    return database_url


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "CreatorTrack API"
    database_url: str = "postgresql+psycopg://creatortrack:creatortrack@db:5432/creatortrack"
    redis_url: str = "redis://redis:6379/0"
    jwt_secret: str = "change-me"
    jwt_algorithm: str = "HS256"
    upload_dir: str = "/app/uploads"
    processed_dir: str = "/app/processed"
    api_base_url: str = "http://localhost:8000"
    frontend_origin: str = "http://localhost:3000"
    cors_allow_all: bool = False
    job_runner_mode: str = "celery"
    startup_db_retries: int = 20
    startup_db_retry_delay_seconds: int = 3


settings = Settings()
settings.database_url = normalize_database_url(settings.database_url)
