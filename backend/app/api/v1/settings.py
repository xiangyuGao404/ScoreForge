"""Settings API endpoints."""

import logging

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import encrypt_api_key
from app.models.user import User
from app.schemas.common import APIResponse
from app.api.deps import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/settings", tags=["设置"])


@router.put("/api-key", response_model=APIResponse)
async def update_api_key(
    body: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """更新用户自备 API Key。"""
    api_key = body.get("api_key", "").strip()

    if not api_key:
        # Clear the API key
        current_user.api_key_encrypted = None
        await db.flush()
        return APIResponse(message="API Key 已清除")

    # Encrypt and store
    try:
        encrypted = encrypt_api_key(api_key)
        current_user.api_key_encrypted = encrypted
        await db.flush()
        logger.info(f"User {current_user.id} updated API key")
        return APIResponse(message="API Key 已保存")
    except Exception as e:
        logger.error(f"Failed to encrypt API key: {e}")
        return APIResponse(code=1, message="API Key 保存失败")
