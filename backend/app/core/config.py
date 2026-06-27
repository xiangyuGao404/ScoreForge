"""Application configuration management."""

import logging
from pydantic_settings import BaseSettings
from typing import Optional

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "ScoreForge"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    ALLOWED_ORIGINS: str = "*"  # S-3: In production, set to specific domains

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://scoreforge:password@localhost:5432/scoreforge"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # JWT
    JWT_SECRET_KEY: str = "dev-jwt-secret-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    # S-6: Reduce JWT expiry in production
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days (dev), reduce to 1-2 days in prod

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
    USER_KEY_ENCRYPTION_KEY: str = "dev-encryption-key-change-in-production"

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

    def validate_production_settings(self):
        """S-2: Validate critical settings in production mode."""
        if not self.DEBUG:
            warnings = []
            if "change-in-production" in self.SECRET_KEY:
                warnings.append("SECRET_KEY is using default value")
            if "change-in-production" in self.JWT_SECRET_KEY:
                warnings.append("JWT_SECRET_KEY is using default value")
            if "change-in-production" in self.USER_KEY_ENCRYPTION_KEY:
                warnings.append("USER_KEY_ENCRYPTION_KEY is using default value")
            if self.ALLOWED_ORIGINS == "*":
                warnings.append("ALLOWED_ORIGINS is set to '*' (insecure)")
            if warnings:
                for w in warnings:
                    logger.warning(f"Security warning: {w}")
                # In strict mode, could raise an error here


settings = Settings()

# Run validation on import
settings.validate_production_settings()
