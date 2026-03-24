from pydantic_settings import BaseSettings, SettingsConfigDict


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
