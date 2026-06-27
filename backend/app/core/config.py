"""Application configuration management."""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "ScoreForge"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    SECRET_KEY: str = "your-jwt-secret-key-change-in-production"
    ALLOWED_ORIGINS: str = "*"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://scoreforge:password@localhost:5432/scoreforge"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # JWT
    JWT_SECRET_KEY: str = "your-jwt-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # SMS (Alibaba Cloud)
    SMS_ACCESS_KEY: Optional[str] = None
    SMS_SECRET_KEY: Optional[str] = None
    SMS_SIGN_NAME: str = "ScoreForge"
    SMS_TEMPLATE_CODE: str = "SMS_XXX"

    # AI API
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_API_BASE: str = "https://api.openai.com/v1"
    DEFAULT_AI_MODEL: str = "gpt-4o"

    # User AI Key Encryption
    USER_KEY_ENCRYPTION_KEY: str = "user-key-encryption-secret"

    # OSS (Alibaba Cloud)
    OSS_ACCESS_KEY: Optional[str] = None
    OSS_SECRET_KEY: Optional[str] = None
    OSS_BUCKET: str = "scoreforge-files"
    OSS_ENDPOINT: str = "oss-cn-hangzhou.aliyuncs.com"
    OSS_CDN_DOMAIN: str = "https://files.scoreforge.app"

    # File Storage
    UPLOAD_DIR: str = "./uploads"
    PDF_DIR: str = "./pdfs"

    # OCR
    OCR_USE_GPU: bool = False

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
