"""PDF generation and download API endpoints."""

import os
import uuid
import logging

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.config import settings
from app.core.exceptions import NotFoundException, ForbiddenException, BadRequestException
from app.models.user import User, Student
from app.models.knowledge import KnowledgePoint
from app.models.weakness import Weakness
from app.models.practice import PracticeSession, PracticeQuestion
from app.schemas.common import APIResponse
from app.schemas.pdf import PDFGenerateRequest, PDFGenerateResponse
from app.api.deps import get_current_user
from app.services.pdf_service import pdf_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/pdf", tags=["PDF"])


def _pdf_owner_key(pdf_id: str) -> str:
    """Redis key for PDF ownership tracking."""
    return f"pdf:owner:{pdf_id}"


@router.post("/generate", response_model=APIResponse[PDFGenerateResponse])
async def generate_pdf(
    req: PDFGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """生成练习题 PDF。"""
    session_id = uuid.UUID(req.session_id)

    # Verify session ownership
    session_result = await db.execute(
        select(PracticeSession, Weakness, KnowledgePoint, Student)
        .join(Weakness, PracticeSession.weakness_id == Weakness.id)
        .join(KnowledgePoint, Weakness.knowledge_point_id == KnowledgePoint.id)
        .join(Student, PracticeSession.student_id == Student.id)
        .where(PracticeSession.id == session_id, Student.user_id == current_user.id)
    )
    session_data = session_result.one_or_none()
    if not session_data:
        raise NotFoundException("练习记录不存在")

    session, weakness, kp, student = session_data

    # Get questions
    questions_result = await db.execute(
        select(PracticeQuestion)
        .where(PracticeQuestion.session_id == session_id)
        .order_by(PracticeQuestion.question_no)
    )
    questions = questions_result.scalars().all()

    if not questions:
        raise BadRequestException("没有可生成PDF的题目")

    # Generate PDF
    try:
        subject_labels = {"math": "数学", "politics": "道法", "history": "历史"}
        subject_label = subject_labels.get(kp.subject, kp.subject)

        pdf_id = str(uuid.uuid4())
        pdf_path = await pdf_service.generate(
            student_name=student.name,
            subject=subject_label,
            weakness_name=kp.name,
            questions=[
                {
                    "question_no": q.question_no,
                    "difficulty": q.difficulty.value,
                    "question_content": q.question_content,
                    "question_type": q.question_type.value if hasattr(q.question_type, 'value') else q.question_type,
                    "reference_answer": q.reference_answer if req.include_answers else "",
                    "solution_detail": q.solution_detail if req.include_solutions else "",
                }
                for q in questions
            ],
            include_answers=req.include_answers,
            include_solutions=req.include_solutions,
            pdf_id=pdf_id,
        )

        # S-4 fix: Store PDF ownership in Redis
        try:
            from app.core.redis import redis_client
            await redis_client.setex(
                _pdf_owner_key(pdf_id),
                86400 * 7,  # 7 days expiry
                str(current_user.id),
            )
        except Exception as e:
            logger.warning(f"Failed to store PDF ownership: {e}")

        # Store filename for download
        filename = f"ScoreForge_{student.name}_{kp.name}_{pdf_id[:8]}.pdf"
        try:
            from app.core.redis import redis_client
            await redis_client.setex(
                f"pdf:name:{pdf_id}",
                86400 * 7,
                filename,
            )
        except Exception:
            pass

        logger.info(f"PDF generated: {pdf_path}")

        return APIResponse(
            data=PDFGenerateResponse(
                pdf_id=pdf_id,
                status="ready",
                message="PDF 生成完成",
            )
        )

    except Exception as e:
        logger.error(f"PDF generation failed: {e}")
        raise BadRequestException("PDF 生成失败，请稍后重试")


@router.get("/{pdf_id}/download")
async def download_pdf(
    pdf_id: str,
    current_user: User = Depends(get_current_user),
):
    """下载 PDF 文件。"""
    # S-4 fix: Verify PDF ownership
    try:
        from app.core.redis import redis_client
        owner_id = await redis_client.get(_pdf_owner_key(pdf_id))
        if owner_id and owner_id != str(current_user.id):
            raise ForbiddenException("无权下载此 PDF")
    except ForbiddenException:
        raise
    except Exception:
        # Redis unavailable, skip ownership check in dev mode
        if not settings.DEBUG:
            raise ForbiddenException("无法验证 PDF 所有权")

    pdf_path = os.path.join(settings.PDF_DIR, f"{pdf_id}.pdf")

    if not os.path.exists(pdf_path):
        raise NotFoundException("PDF 文件不存在")

    # Get filename from Redis or use default
    filename = f"ScoreForge_练习题_{pdf_id[:8]}.pdf"
    try:
        from app.core.redis import redis_client
        stored_name = await redis_client.get(f"pdf:name:{pdf_id}")
        if stored_name:
            filename = stored_name
    except Exception:
        pass

    return FileResponse(
        path=pdf_path,
        filename=filename,
        media_type="application/pdf",
    )
