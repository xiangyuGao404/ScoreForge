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
    ALLOWED_ORIGINS: str = "*"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://scoreforge:password@localhost:5432/scoreforge"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # JWT
    JWT_SECRET_KEY: str = "dev-jwt-secret-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7

    # SMS (Alibaba Cloud)
    SMS_ACCESS_KEY: Optional[str] = None
    SMS_SECRET_KEY: Optional[str] = None
    SMS_SIGN_NAME: str = "ScoreForge"
    SMS_TEMPLATE_CODE: str = "SMS_XXX"

    # ===== AI 平台配置（系统级默认值，可被用户配置覆盖） =====
    AI_PROVIDER: str = "xiaomi"  # xiaomi / deepseek / openai

    # 小米 TokenPlan
    XIAOMI_API_KEY: Optional[str] = None
    XIAOMI_API_BASE: str = "https://token-plan-cn.xiaomimimo.com/v1"
    XIAOMI_GENERAL_MODEL: str = "mimo-v2.5-pro"      # 通用：分析、出题、评估
    XIAOMI_VISION_MODEL: str = "mimo-v2.5"            # 图片识别

    # DeepSeek
    DEEPSEEK_API_KEY: Optional[str] = None
    DEEPSEEK_API_BASE: str = "https://api.deepseek.com/v1"
    DEEPSEEK_GENERAL_MODEL: str = "deepseek-v4-flash"
    DEEPSEEK_VISION_MODEL: str = "DeepSeek-VL2"

    # OpenAI 兼容（用户自填）
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_API_BASE: str = "https://api.openai.com/v1"
    OPENAI_GENERAL_MODEL: str = "gpt-4o"
    OPENAI_VISION_MODEL: str = "gpt-4o"

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

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    def validate_production_settings(self):
        """Validate critical settings in production mode."""
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


settings = Settings()

# Run validation on import
settings.validate_production_settings()
