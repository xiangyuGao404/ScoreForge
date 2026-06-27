"""Weakness management API endpoints."""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import NotFoundException, ForbiddenException
from app.models.user import User, Student
from app.models.knowledge import KnowledgePoint
from app.models.weakness import Weakness, WeaknessStatus
from app.schemas.common import APIResponse
from app.api.deps import get_current_user

router = APIRouter(prefix="/weaknesses", tags=["薄弱点"])


@router.get("")
async def list_weaknesses(
    student_id: uuid.UUID,
    status: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取薄弱点列表。"""
    # Verify student ownership
    student_result = await db.execute(select(Student).where(Student.id == student_id))
    student = student_result.scalar_one_or_none()
    if not student or student.user_id != current_user.id:
        raise NotFoundException("孩子档案不存在")

    query = (
        select(Weakness, KnowledgePoint)
        .join(KnowledgePoint, Weakness.knowledge_point_id == KnowledgePoint.id)
        .where(Weakness.student_id == student_id)
    )

    if status:
        try:
            ws = WeaknessStatus(status)
            query = query.where(Weakness.status == ws)
        except ValueError:
            pass

    query = query.order_by(Weakness.star_rating.desc())
    result = await db.execute(query)
    weaknesses = result.all()

    return APIResponse(
        data={
            "weaknesses": [
                {
                    "weakness_id": str(w.id),
                    "knowledge_point": kp.name,
                    "star_rating": w.star_rating,
                    "reason": w.reason or "",
                    "status": w.status.value,
                    "mastery_score": w.mastery_score,
                    "practice_days": w.practice_days,
                    "recommended_days": w.recommended_days,
                }
                for w, kp in weaknesses
            ]
        }
    )


@router.post("/{weakness_id}/master")
async def mark_mastered(
    weakness_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """标记薄弱点为已掌握。"""
    result = await db.execute(
        select(Weakness)
        .join(Student, Weakness.student_id == Student.id)
        .where(Weakness.id == weakness_id, Student.user_id == current_user.id)
    )
    weakness = result.scalar_one_or_none()

    if weakness is None:
        raise NotFoundException("薄弱点不存在")

    weakness.status = WeaknessStatus.MASTERED
    weakness.mastery_score = 100
    weakness.mastered_at = datetime.now(timezone.utc)
    await db.flush()

    return APIResponse(message="已标记为掌握")
