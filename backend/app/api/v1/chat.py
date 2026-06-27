"""Chat API endpoints for teacher dialogue."""

import uuid
import logging

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import NotFoundException, ForbiddenException, BadRequestException
from app.models.user import User, Student
from app.models.chat import ChatMessage, TeacherRole, ChatRole
from app.schemas.common import APIResponse
from app.schemas.chat import ChatSendRequest, ChatMessageResponse, ChatHistoryResponse
from app.api.deps import get_current_user
from app.services.chat_service import get_teacher_response, TEACHER_PROMPTS

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat", tags=["教师对话"])


@router.post("/send", response_model=APIResponse[ChatMessageResponse])
async def send_message(
    req: ChatSendRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """发送教师对话消息并获取 AI 回复。"""
    # Validate teacher role
    valid_roles = ["math", "politics", "history", "homeroom"]
    if req.teacher_role not in valid_roles:
        raise BadRequestException(f"不支持的教师角色：{req.teacher_role}，支持：{', '.join(valid_roles)}")

    # Verify student ownership
    student_result = await db.execute(
        select(Student).where(Student.id == uuid.UUID(req.student_id))
    )
    student = student_result.scalar_one_or_none()
    if not student or student.user_id != current_user.id:
        raise NotFoundException("孩子档案不存在")

    # Save user message
    user_msg = ChatMessage(
        student_id=uuid.UUID(req.student_id),
        user_id=current_user.id,
        teacher_role=TeacherRole(req.teacher_role),
        role=ChatRole.USER,
        content=req.content,
    )
    db.add(user_msg)
    await db.flush()

    # Get chat history for context
    history_result = await db.execute(
        select(ChatMessage)
        .where(
            ChatMessage.student_id == uuid.UUID(req.student_id),
            ChatMessage.teacher_role == TeacherRole(req.teacher_role),
        )
        .order_by(ChatMessage.created_at.desc())
        .limit(10)
    )
    history = [
        {"role": msg.role.value, "content": msg.content}
        for msg in reversed(history_result.scalars().all())
    ]

    # Get AI response
    ai_response = await get_teacher_response(
        teacher_role=req.teacher_role,
        student_name=student.name,
        grade=student.grade.value,
        user_message=req.content,
        history=history,
    )

    # Save AI response
    ai_msg = ChatMessage(
        student_id=uuid.UUID(req.student_id),
        user_id=current_user.id,
        teacher_role=TeacherRole(req.teacher_role),
        role=ChatRole.ASSISTANT,
        content=ai_response,
    )
    db.add(ai_msg)
    await db.flush()

    return APIResponse(
        data=ChatMessageResponse(
            id=str(ai_msg.id),
            role="assistant",
            content=ai_response,
            created_at=ai_msg.created_at,
        )
    )


@router.get("/history", response_model=APIResponse[ChatHistoryResponse])
async def get_history(
    student_id: str = Query(...),
    teacher_role: str = Query(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取对话历史。"""
    # Validate teacher role
    valid_roles = ["math", "politics", "history", "homeroom"]
    if teacher_role not in valid_roles:
        raise BadRequestException(f"不支持的教师角色：{teacher_role}")

    # Verify student ownership
    student_result = await db.execute(
        select(Student).where(Student.id == uuid.UUID(student_id))
    )
    student = student_result.scalar_one_or_none()
    if not student or student.user_id != current_user.id:
        raise NotFoundException("孩子档案不存在")

    # Get chat history
    result = await db.execute(
        select(ChatMessage)
        .where(
            ChatMessage.student_id == uuid.UUID(student_id),
            ChatMessage.teacher_role == TeacherRole(teacher_role),
        )
        .order_by(ChatMessage.created_at)
        .limit(50)
    )
    messages = result.scalars().all()

    return APIResponse(
        data=ChatHistoryResponse(
            messages=[
                ChatMessageResponse(
                    id=str(msg.id),
                    role=msg.role.value,
                    content=msg.content,
                    created_at=msg.created_at,
                )
                for msg in messages
            ]
        )
    )
