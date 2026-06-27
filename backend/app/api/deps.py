"""API dependencies: authentication, database session, etc."""

from typing import Optional
import uuid

from fastapi import Depends, Header
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_access_token
from app.core.exceptions import UnauthorizedException
from app.models.user import User


async def get_current_user(
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Extract and validate the current user from the Authorization header."""
    if not authorization or not authorization.startswith("Bearer "):
        raise UnauthorizedException()

    token = authorization.split(" ", 1)[1]
    payload = decode_access_token(token)
    if payload is None:
        raise UnauthorizedException("登录已过期，请重新登录")

    user_id = payload.get("sub")
    if user_id is None:
        raise UnauthorizedException()

    try:
        uid = uuid.UUID(user_id)
    except ValueError:
        raise UnauthorizedException()

    result = await db.execute(select(User).where(User.id == uid))
    user = result.scalar_one_or_none()
    if user is None:
        raise UnauthorizedException("用户不存在")

    return user
