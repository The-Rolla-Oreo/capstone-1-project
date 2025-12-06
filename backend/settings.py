from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # JWT Stuff
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int

    # MongoDB Stuff
    MONGO_URI: str
    DB_NAME: str
    USERS_COLLECTION: str
    GROUPS_COLLECTION: str
    PASSWORD_RESET_COLLECTION: str
    EMAIL_VERIFICATION_COLLECTION: str
    GROUP_INVITES_COLLECTION: str
    CHORES_COLLECTION: str

    # S3 Stuff
    S3_ENDPOINT: str
    S3_ACCESS_KEY: str
    S3_SECRET_KEY: str
    S3_BUCKET_NAME: str

    # Email stuff
    SMTP_HOST: str
    SMTP_PORT: int
    SMTP_USERNAME: str
    SMTP_PASSWORD: str

    # Frontend Stuff
    FRONTEND_URL: str

    DEV_MODE: bool
    DEV_USER: str

    # Celery Stuff
    CELERY_BROKER_URL: str

    # Configure code to read from .env file in the backend dir
    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parent / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached settings loaded from environment/.env."""
    return Settings()
