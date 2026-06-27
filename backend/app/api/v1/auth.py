"""Authentication API endpoints."""

import logging

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.redis import get_redis, redis_client
from app.core.security import (
    create_access_token,
    generate_sms_code,
    get_sms_code_key,
    get_sms_rate_limit_key,
)
from app.core.exceptions import BadRequestException, TooManyRequestsException
from app.models.user import User
from app.schemas.common import APIResponse
from app.schemas.auth import SendCodeRequest, LoginRequest, LoginResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/send-code", response_model=APIResponse)
async def send_sms_code(
    req: SendCodeRequest,
    redis=Depends(get_redis),
):
    """
    发送短信验证码。
    开发模式下验证码固定为 888888，并打印到日志。
    """
    phone = req.phone.strip()
    if not phone or len(phone) < 11:
        raise BadRequestException("手机号格式不正确")

    # Rate limiting: 1 code per 60 seconds
    rate_key = get_sms_rate_limit_key(phone)
    if await redis.exists(rate_key):
        raise TooManyRequestsException("验证码发送过于频繁，请60秒后重试")

    # Generate and store code
    code = generate_sms_code()
    code_key = get_sms_code_key(phone)

    # Development mode: use fixed code
    code = "888888"

    await redis.setex(code_key, 300, code)  # 5 min expiry
    await redis.setex(rate_key, 60, "1")  # 60s rate limit

    logger.info(f"SMS code for {phone}: {code}")

    # TODO: In production, call Alibaba Cloud SMS API
    # sms_service.send_sms(phone, code)

    return APIResponse(message="验证码已发送")


@router.post("/login", response_model=APIResponse[LoginResponse])
async def login(
    req: LoginRequest,
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
):
    """
    手机号 + 验证码登录/注册。
    验证码正确后自动创建用户（如果不存在）。
    """
    phone = req.phone.strip()
    code = req.code.strip()

    if not phone or not code:
        raise BadRequestException("手机号和验证码不能为空")

    # Verify code
    code_key = get_sms_code_key(phone)
    stored_code = await redis.get(code_key)

    # Development mode: accept 888888 always
    if code != "888888" and (stored_code is None or stored_code != code):
        raise BadRequestException("验证码错误或已过期")

    # Delete used code
    await redis.delete(code_key)

    # Find or create user
    result = await db.execute(select(User).where(User.phone == phone))
    user = result.scalar_one_or_none()

    if user is None:
        user = User(phone=phone, nickname=f"家长{phone[-4:]}")
        db.add(user)
        await db.flush()
        logger.info(f"New user registered: {phone}")

    # Create JWT token
    token = create_access_token(data={"sub": str(user.id)})

    return APIResponse(
        data=LoginResponse(
            token=token,
            user_id=str(user.id),
            nickname=user.nickname,
            user_level=user.user_level.value,
        )
    )
