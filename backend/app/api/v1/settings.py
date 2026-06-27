"""Settings API endpoints: API config, test connection."""

import json
import logging
import time

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.config import settings
from app.core.security import encrypt_api_key, decrypt_api_key
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
    """更新用户自备 API Key（简单模式）。"""
    api_key = body.get("api_key", "").strip()

    if not api_key:
        current_user.api_key_encrypted = None
        await db.flush()
        return APIResponse(message="API Key 已清除")

    try:
        encrypted = encrypt_api_key(api_key)
        current_user.api_key_encrypted = encrypted
        await db.flush()
        logger.info(f"User {current_user.id} updated API key")
        return APIResponse(message="API Key 已保存")
    except Exception as e:
        logger.error(f"Failed to encrypt API key: {e}")
        return APIResponse(code=1, message="API Key 保存失败")


@router.get("/api-config", response_model=APIResponse)
async def get_api_config(
    current_user: User = Depends(get_current_user),
):
    """获取用户 API 配置（不返回实际 Key）。"""
    config = _get_user_config_sync(current_user)

    return APIResponse(
        data={
            "provider": config.get("provider", settings.AI_PROVIDER),
            "api_key_set": bool(config.get("api_key")),
            "api_base": config.get("api_base", ""),
            "general_model": config.get("general_model", ""),
            "vision_model": config.get("vision_model", ""),
        }
    )


@router.put("/api-config", response_model=APIResponse)
async def save_api_config(
    body: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """保存用户 API 配置（完整模式）。"""
    provider = body.get("provider", "xiaomi")
    api_key = body.get("api_key", "").strip()
    api_base = body.get("api_base", "").strip()
    general_model = body.get("general_model", "").strip()
    vision_model = body.get("vision_model", "").strip()

    if not api_key:
        # Clear config
        current_user.api_config_encrypted = None
        await db.flush()
        return APIResponse(message="API 配置已清除")

    # Build config dict
    config = {
        "provider": provider,
        "api_key": api_key,
        "api_base": api_base,
        "general_model": general_model,
        "vision_model": vision_model,
    }

    try:
        encrypted = encrypt_api_key(json.dumps(config))
        current_user.api_config_encrypted = encrypted
        await db.flush()
        logger.info(f"User {current_user.id} saved API config: provider={provider}")
        return APIResponse(message="配置已保存")
    except Exception as e:
        logger.error(f"Failed to save API config: {e}")
        return APIResponse(code=1, message="配置保存失败")


@router.post("/test-api", response_model=APIResponse)
async def test_api_connection(
    body: dict,
    current_user: User = Depends(get_current_user),
):
    """测试 API 连接。"""
    from openai import AsyncOpenAI

    provider = body.get("provider")
    api_key = body.get("api_key")
    api_base = body.get("api_base")
    model = body.get("model")
    task_type = body.get("task_type", "general")

    # If no params provided, use user's saved config
    if not api_key:
        config = _get_user_config_sync(current_user)
        if not config.get("api_key"):
            return APIResponse(code=1, message="未配置 API Key，请先填写配置")
        provider = config.get("provider", settings.AI_PROVIDER)
        api_key = config["api_key"]
        api_base = config.get("api_base", "")
        model_key = f"{task_type}_model"
        model = config.get(model_key, "")

    # Set defaults based on provider
    if not api_base:
        if provider == "xiaomi":
            api_base = settings.XIAOMI_API_BASE
        elif provider == "deepseek":
            api_base = settings.DEEPSEEK_API_BASE
        else:
            api_base = settings.OPENAI_API_BASE

    if not model:
        if provider == "xiaomi":
            model = settings.XIAOMI_VISION_MODEL if task_type == "vision" else settings.XIAOMI_GENERAL_MODEL
        elif provider == "deepseek":
            model = settings.DEEPSEEK_VISION_MODEL if task_type == "vision" else settings.DEEPSEEK_GENERAL_MODEL
        else:
            model = settings.OPENAI_VISION_MODEL if task_type == "vision" else settings.OPENAI_GENERAL_MODEL

    # Test connection
    try:
        client = AsyncOpenAI(api_key=api_key, base_url=api_base, timeout=30.0)

        start_time = time.time()
        response = await client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "请回复OK"}],
            max_tokens=10,
        )
        latency_ms = int((time.time() - start_time) * 1000)

        preview = response.choices[0].message.content[:50]

        return APIResponse(
            data={
                "success": True,
                "model": model,
                "response_preview": preview,
                "latency_ms": latency_ms,
            }
        )

    except Exception as e:
        error_msg = str(e)
        # Clean up error message
        if "401" in error_msg or "Unauthorized" in error_msg:
            error_msg = "API Key 无效或已过期"
        elif "404" in error_msg or "Not Found" in error_msg:
            error_msg = f"模型 '{model}' 不存在或不支持"
        elif "timeout" in error_msg.lower():
            error_msg = "连接超时，请检查网络或 API 地址"
        elif "Connection" in error_msg:
            error_msg = "无法连接到 API 服务器，请检查 API 地址"

        logger.error(f"API test failed: {e}")

        return APIResponse(
            code=1,
            data={
                "success": False,
                "model": model,
                "error": error_msg,
            }
        )


def _get_user_config_sync(user: User) -> dict:
    """Get user's API config from encrypted field."""
    if user.api_config_encrypted:
        try:
            decrypted = decrypt_api_key(user.api_config_encrypted)
            return json.loads(decrypted)
        except Exception:
            pass
    return {}
