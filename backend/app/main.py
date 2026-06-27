"""FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.exceptions import AppException
from app.api.v1 import api_v1_router

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Default AI Provider: {settings.AI_PROVIDER}")
    logger.info(f"Xiaomi configured: {bool(settings.XIAOMI_API_KEY)}")
    logger.info(f"DeepSeek configured: {bool(settings.DEEPSEEK_API_KEY)}")
    logger.info(f"OpenAI configured: {bool(settings.OPENAI_API_KEY)}")
    logger.info(f"CORS origins: {settings.ALLOWED_ORIGINS}")
    # Create upload and PDF directories
    import os
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs(settings.PDF_DIR, exist_ok=True)
    yield
    logger.info(f"Shutting down {settings.APP_NAME}")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="ScoreForge - AI 学情诊断工具后端 API",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# S-3 fix: CORS configuration
# In production, ALLOWED_ORIGINS should be specific domains, not "*"
# allow_credentials cannot be used with wildcard origins
cors_origins = settings.ALLOWED_ORIGINS.split(",")
allow_credentials = cors_origins != ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    """Handle application exceptions with consistent format."""
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.detail,
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    logger.exception(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"code": 500, "message": "服务器内部错误", "detail": str(exc) if settings.DEBUG else ""},
    )


# Include API router
app.include_router(api_v1_router)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
    }


@app.get("/health")
async def health_check():
    """Detailed health check."""
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "debug": settings.DEBUG,
    }


@app.get("/ai-status")
async def ai_status():
    """Check AI service configuration status (no secrets exposed)."""
    provider = settings.AI_PROVIDER.lower()

    providers = {
        "xiaomi": {
            "configured": bool(settings.XIAOMI_API_KEY),
            "general_model": settings.XIAOMI_GENERAL_MODEL,
            "vision_model": settings.XIAOMI_VISION_MODEL,
        },
        "deepseek": {
            "configured": bool(settings.DEEPSEEK_API_KEY),
            "general_model": settings.DEEPSEEK_GENERAL_MODEL,
            "vision_model": settings.DEEPSEEK_VISION_MODEL,
        },
        "openai": {
            "configured": bool(settings.OPENAI_API_KEY),
            "general_model": settings.OPENAI_GENERAL_MODEL,
            "vision_model": settings.OPENAI_VISION_MODEL,
        },
    }

    return {
        "default_provider": provider,
        "providers": providers,
        "timeout_seconds": 60,
        "max_retries": 2,
        "fallback": "mock data on failure",
    }
