"""Practice API endpoints: generate, questions, submit, assessment."""

import uuid
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db, async_session_factory
from app.core.exceptions import NotFoundException, BadRequestException
from app.models.user import User, Student
from app.models.knowledge import KnowledgePoint
from app.models.weakness import Weakness, WeaknessStatus
from app.models.practice import (
    PracticeSession, PracticeQuestion, PracticeMode, Difficulty, MasteryStatus, PracticeStatus, QuestionType
)
from app.schemas.common import APIResponse
from app.schemas.practice import (
    PracticeGenerateRequest, PracticeGenerateResponse,
    PracticeQuestionResponse, PracticeQuestionsResponse,
    PracticeSubmitRequest, PracticeSubmitResponse,
    PracticeAssessmentResponse, HistoryItem,
)
from app.api.deps import get_current_user
from app.services.ai_service import ai_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/practice", tags=["练习"])


# ─── 后台任务 ─────────────────────────────────────────────────


async def _run_generate_background(session_id: str, kp_name: str, subject: str, grade: str,
                                    question_count: int, student_id: str, weakness_id: str, user_id: str):
    """后台执行 AI 出题。"""
    async with async_session_factory() as db:
        try:
            from app.services.ai_service import ai_service as ai

            historical_result = await db.execute(
                select(PracticeQuestion.question_content).join(PracticeSession)
                .where(PracticeSession.student_id == uuid.UUID(student_id),
                       PracticeSession.weakness_id == uuid.UUID(weakness_id)).limit(50)
            )
            historical_qs = [row[0] for row in historical_result.all()]

            questions_data = await ai.generate_questions(
                knowledge_point=kp_name, subject=subject, grade=grade,
                question_count=question_count, historical_questions=historical_qs,
                db=db, user_id=user_id,
            )

            difficulty_map = {"basic": Difficulty.BASIC, "medium": Difficulty.MEDIUM, "advanced": Difficulty.ADVANCED}
            type_map = {"choice": QuestionType.CHOICE, "fill_blank": QuestionType.FILL_BLANK, "solve": QuestionType.SOLVE}

            for qd in questions_data:
                db.add(PracticeQuestion(session_id=uuid.UUID(session_id),
                    question_no=qd["question_no"], question_content=qd["question_content"],
                    reference_answer=qd["reference_answer"], solution_detail=qd["solution_detail"],
                    difficulty=difficulty_map.get(qd.get("difficulty", "basic"), Difficulty.BASIC),
                    question_type=type_map.get(qd.get("question_type", "solve"), QuestionType.SOLVE)))

            session = await db.get(PracticeSession, uuid.UUID(session_id))
            if session:
                session.status = PracticeStatus.READY
            await db.commit()
            logger.info(f"Generate background: session {session_id} ready ({len(questions_data)} questions)")

        except Exception as e:
            logger.error(f"Generate background failed for session {session_id}: {e}")
            try:
                s = await db.get(PracticeSession, uuid.UUID(session_id))
                if s:
                    s.status = PracticeStatus.READY
                    await db.commit()
            except Exception:
                pass


async def _run_assessment_background(session_id: str, user_id: str):
    """后台执行掌握度评估。"""
    async with async_session_factory() as db:
        try:
            session = await db.get(PracticeSession, uuid.UUID(session_id))
            if not session:
                return

            s_result = await db.execute(
                select(Student, Weakness, KnowledgePoint)
                .join(Weakness, PracticeSession.weakness_id == Weakness.id)
                .join(KnowledgePoint, Weakness.knowledge_point_id == KnowledgePoint.id)
                .where(PracticeSession.id == session.id)
            )
            row = s_result.one_or_none()
            if not row:
                return
            student, weakness, kp = row

            wrong_result = await db.execute(
                select(PracticeQuestion).where(PracticeQuestion.session_id == session.id, PracticeQuestion.is_correct == False)
            )
            wrong_details = [{"question_no": q.question_no, "question_content": q.question_content, "student_answer": q.student_answer}
                             for q in wrong_result.scalars().all()]

            assessment = await ai_service.assess_mastery(
                student_name=student.name, grade=student.grade.value,
                knowledge_point=kp.name, practice_history=[],
                correct_count=int(session.correct_rate * session.question_count) if session.correct_rate else 0,
                total_count=session.question_count, wrong_details=wrong_details,
                db=db, user_id=user_id,
            )

            weakness.mastery_score = assessment.get("mastery_score", 0)
            weakness.recommended_days = assessment.get("suggested_days", 2)
            if assessment.get("recommendation") == "mastered":
                weakness.status = WeaknessStatus.MASTERED
                weakness.mastered_at = datetime.now(timezone.utc)

            session.ai_assessment = assessment
            session.status = PracticeStatus.ASSESSED
            await db.commit()
            logger.info(f"Assessment background: session {session_id} completed")

        except Exception as e:
            logger.error(f"Assessment background failed for session {session_id}: {e}")
            try:
                s = await db.get(PracticeSession, uuid.UUID(session_id))
                if s:
                    s.status = PracticeStatus.ASSESSED
                    await db.commit()
            except Exception:
                pass


# ─── 端点 ────────────────────────────────────────────────────


@router.post("/generate", response_model=APIResponse[PracticeGenerateResponse])
async def generate_practice(
    req: PracticeGenerateRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """生成练习题 → 立即返回 generating → 后台 AI 出题。
    前端轮询 GET /practice/{id}/questions 直到 status=ready。"""
    student_result = await db.execute(select(Student).where(Student.id == uuid.UUID(req.student_id)))
    student = student_result.scalar_one_or_none()
    if not student or student.user_id != current_user.id:
        raise NotFoundException("孩子档案不存在")

    weakness_result = await db.execute(
        select(Weakness, KnowledgePoint).join(KnowledgePoint)
        .where(Weakness.id == uuid.UUID(req.weakness_id), Weakness.student_id == uuid.UUID(req.student_id))
    )
    weakness_data = weakness_result.one_or_none()
    if not weakness_data:
        raise NotFoundException("薄弱点不存在")
    weakness, kp = weakness_data

    mode = PracticeMode(req.mode) if req.mode in ("online", "pdf") else PracticeMode.ONLINE

    session = PracticeSession(student_id=uuid.UUID(req.student_id), weakness_id=uuid.UUID(req.weakness_id),
        mode=mode, question_count=req.question_count, status=PracticeStatus.GENERATING)
    db.add(session)
    await db.flush()

    background_tasks.add_task(
        _run_generate_background, str(session.id), kp.name, kp.subject,
        student.grade.value, req.question_count, req.student_id, req.weakness_id, str(current_user.id)
    )

    if weakness.status == WeaknessStatus.NOT_STARTED:
        weakness.status = WeaknessStatus.PRACTICING
        await db.flush()

    return APIResponse(data=PracticeGenerateResponse(session_id=str(session.id),
        mode=mode.value, status=PracticeStatus.GENERATING.value, message="正在生成题目"))


@router.get("/{session_id}/questions")
async def get_questions(
    session_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取题目列表（供前端轮询）。
    - generating: 生成中，questions 为空
    - ready: 完成，questions 有数据"""
    result = await db.execute(
        select(PracticeSession, Weakness, KnowledgePoint).join(Weakness).join(KnowledgePoint).join(Student)
        .where(PracticeSession.id == session_id, Student.user_id == current_user.id)
    )
    session_data = result.one_or_none()
    if not session_data:
        raise NotFoundException("练习记录不存在")
    session, weakness, kp = session_data

    if session.status == PracticeStatus.GENERATING:
        return APIResponse(data=PracticeQuestionsResponse(
            session_id=str(session.id), weakness=kp.name, questions=[]),
            message="正在生成题目中")

    questions_result = await db.execute(
        select(PracticeQuestion).where(PracticeQuestion.session_id == session_id).order_by(PracticeQuestion.question_no)
    )
    return APIResponse(data=PracticeQuestionsResponse(
        session_id=str(session.id), weakness=kp.name,
        questions=[PracticeQuestionResponse.model_validate(q) for q in questions_result.scalars().all()]))


@router.post("/{session_id}/submit", response_model=APIResponse[PracticeSubmitResponse])
async def submit_practice(
    session_id: uuid.UUID,
    req: PracticeSubmitRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """提交做题结果 → 立即返回 assessing → 后台 AI 评估。
    前端轮询 GET /practice/{id}/assessment 直到 status=assessed。"""
    session_result = await db.execute(
        select(PracticeSession).join(Student).where(PracticeSession.id == session_id, Student.user_id == current_user.id)
    )
    session = session_result.scalar_one_or_none()
    if not session:
        raise NotFoundException("练习记录不存在")

    questions_result = await db.execute(
        select(PracticeQuestion).where(PracticeQuestion.session_id == session_id)
    )
    questions_map = {q.question_no: q for q in questions_result.scalars().all()}

    correct_count = 0
    total_count = len(req.results)
    for r in req.results:
        q = questions_map.get(r.question_no)
        if q:
            q.student_answer = r.student_answer
            q.is_correct = r.is_correct
            q.parent_marked = True
            if r.is_correct:
                correct_count += 1

    session.correct_rate = correct_count / total_count if total_count > 0 else 0
    session.status = PracticeStatus.ASSESSING
    await db.flush()
    await db.commit()

    background_tasks.add_task(_run_assessment_background, str(session_id), str(current_user.id))

    return APIResponse(data=PracticeSubmitResponse(session_id=str(session.id),
        correct_rate=session.correct_rate, assessment_status=PracticeStatus.ASSESSING.value,
        message="正在评估掌握程度"))


@router.get("/{session_id}/assessment")
async def get_assessment(
    session_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取掌握度评估（供前端轮询）。
    - assessing: 评估中
    - assessed: 完成"""
    result = await db.execute(
        select(PracticeSession, Weakness, KnowledgePoint, Student)
        .join(Weakness).join(KnowledgePoint).join(Student)
        .where(PracticeSession.id == session_id, Student.user_id == current_user.id)
    )
    session_data = result.one_or_none()
    if not session_data:
        raise NotFoundException("练习记录不存在")
    session, weakness, kp, student = session_data

    if session.correct_rate is None:
        raise BadRequestException("尚未提交做题结果")

    if session.status == PracticeStatus.ASSESSING:
        return APIResponse(data=PracticeAssessmentResponse(
            session_id=str(session.id), mastery_score=weakness.mastery_score,
            trend="stable", error_pattern="", recommendation="continue",
            suggested_days=2, suggestion_detail="AI 正在评估中", history=[]),
            message="AI 正在评估中")

    history_result = await db.execute(
        select(PracticeSession).where(PracticeSession.weakness_id == weakness.id,
            PracticeSession.correct_rate.isnot(None)).order_by(PracticeSession.created_at)
    )
    history = [HistoryItem(date=s.created_at.strftime("%Y-%m-%d"),
        correct_rate=s.correct_rate or 0, mastery_score=weakness.mastery_score)
        for s in history_result.scalars().all()]

    assessment = session.ai_assessment or {
        "mastery_score": int((session.correct_rate or 0) * 100),
        "trend": "stable", "error_pattern": "其他", "recommendation": "continue",
        "suggested_days": 2, "suggestion_detail": "请继续练习以巩固知识",
    }

    return APIResponse(data=PracticeAssessmentResponse(
        session_id=str(session.id), mastery_score=assessment.get("mastery_score", 0),
        trend=assessment.get("trend", "stable"), error_pattern=assessment.get("error_pattern", ""),
        recommendation=assessment.get("recommendation", "continue"),
        suggested_days=assessment.get("suggested_days", 2),
        suggestion_detail=assessment.get("suggestion_detail", ""), history=history))
