"""Practice API endpoints: generate, questions, submit, assessment."""

import uuid
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import NotFoundException, ForbiddenException, BadRequestException
from app.models.user import User, Student
from app.models.knowledge import KnowledgePoint
from app.models.weakness import Weakness, WeaknessStatus
from app.models.practice import PracticeSession, PracticeQuestion, PracticeMode, Difficulty, MasteryStatus, QuestionType
from app.models.exam import Exam
from app.schemas.common import APIResponse
from app.schemas.practice import (
    PracticeGenerateRequest,
    PracticeGenerateResponse,
    PracticeQuestionResponse,
    PracticeQuestionsResponse,
    PracticeSubmitRequest,
    PracticeSubmitResponse,
    PracticeAssessmentResponse,
    HistoryItem,
)
from app.api.deps import get_current_user
from app.services.ai_service import ai_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/practice", tags=["练习"])


@router.post("/generate", response_model=APIResponse[PracticeGenerateResponse])
async def generate_practice(
    req: PracticeGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """生成练习题。"""
    # Verify student ownership
    student_result = await db.execute(select(Student).where(Student.id == req.student_id))
    student = student_result.scalar_one_or_none()
    if not student or student.user_id != current_user.id:
        raise NotFoundException("孩子档案不存在")

    # Verify weakness ownership
    weakness_result = await db.execute(
        select(Weakness, KnowledgePoint)
        .join(KnowledgePoint, Weakness.knowledge_point_id == KnowledgePoint.id)
        .where(Weakness.id == req.weakness_id, Weakness.student_id == req.student_id)
    )
    weakness_data = weakness_result.one_or_none()
    if not weakness_data:
        raise NotFoundException("薄弱点不存在")

    weakness, kp = weakness_data

    # Validate mode
    mode = PracticeMode(req.mode) if req.mode in ("online", "pdf") else PracticeMode.ONLINE

    # Create practice session
    session = PracticeSession(
        student_id=req.student_id,
        weakness_id=req.weakness_id,
        mode=mode,
        question_count=req.question_count,
    )
    db.add(session)
    await db.flush()

    # Generate questions via AI
    try:
        # Get historical questions to avoid repetition
        historical_result = await db.execute(
            select(PracticeQuestion.question_content)
            .join(PracticeSession)
            .where(
                PracticeSession.student_id == req.student_id,
                PracticeSession.weakness_id == req.weakness_id,
            )
            .limit(50)
        )
        historical_questions = [row[0] for row in historical_result.all()]

        questions_data = await ai_service.generate_questions(
            knowledge_point=kp.name,
            subject=kp.subject,
            grade=student.grade.value,
            question_count=req.question_count,
            historical_questions=historical_questions,
            db=db,
            user_id=str(current_user.id),
        )

        # Create practice questions
        difficulty_map = {"basic": Difficulty.BASIC, "medium": Difficulty.MEDIUM, "advanced": Difficulty.ADVANCED}
        question_type_map = {"choice": QuestionType.CHOICE, "fill_blank": QuestionType.FILL_BLANK, "solve": QuestionType.SOLVE}

        for q_data in questions_data:
            pq = PracticeQuestion(
                session_id=session.id,
                question_no=q_data["question_no"],
                question_content=q_data["question_content"],
                reference_answer=q_data["reference_answer"],
                solution_detail=q_data["solution_detail"],
                difficulty=difficulty_map.get(q_data.get("difficulty", "basic"), Difficulty.BASIC),
                question_type=question_type_map.get(q_data.get("question_type", "solve"), QuestionType.SOLVE),
            )
            db.add(pq)

        await db.flush()
        logger.info(f"Practice session {session.id} generated {len(questions_data)} questions")

    except Exception as e:
        logger.error(f"Question generation failed for session {session.id}: {e}")
        raise BadRequestException("题目生成失败，请稍后重试")

    # L-3 fix: use enum member instead of string
    if weakness.status == WeaknessStatus.NOT_STARTED:
        weakness.status = WeaknessStatus.PRACTICING
        await db.flush()

    # L-4 fix: remove dead code, status is always "ready" after generation
    return APIResponse(
        data=PracticeGenerateResponse(
            session_id=str(session.id),
            mode=mode.value,
            status="ready",
            message="题目生成完成",
        )
    )


@router.get("/{session_id}/questions", response_model=APIResponse[PracticeQuestionsResponse])
async def get_questions(
    session_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取练习题列表。"""
    # Verify session ownership
    session_result = await db.execute(
        select(PracticeSession, Weakness, KnowledgePoint)
        .join(Weakness, PracticeSession.weakness_id == Weakness.id)
        .join(KnowledgePoint, Weakness.knowledge_point_id == KnowledgePoint.id)
        .join(Student, PracticeSession.student_id == Student.id)
        .where(PracticeSession.id == session_id, Student.user_id == current_user.id)
    )
    session_data = session_result.one_or_none()
    if not session_data:
        raise NotFoundException("练习记录不存在")

    session, weakness, kp = session_data

    # Get questions
    questions_result = await db.execute(
        select(PracticeQuestion)
        .where(PracticeQuestion.session_id == session_id)
        .order_by(PracticeQuestion.question_no)
    )
    questions = questions_result.scalars().all()

    return APIResponse(
        data=PracticeQuestionsResponse(
            session_id=str(session.id),
            weakness=kp.name,
            questions=[PracticeQuestionResponse.model_validate(q) for q in questions],
        )
    )


@router.post("/{session_id}/submit", response_model=APIResponse[PracticeSubmitResponse])
async def submit_practice(
    session_id: uuid.UUID,
    req: PracticeSubmitRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """提交做题结果。"""
    # Verify session ownership
    session_result = await db.execute(
        select(PracticeSession)
        .join(Student, PracticeSession.student_id == Student.id)
        .where(PracticeSession.id == session_id, Student.user_id == current_user.id)
    )
    session = session_result.scalar_one_or_none()
    if not session:
        raise NotFoundException("练习记录不存在")

    # Update questions with results
    questions_result = await db.execute(
        select(PracticeQuestion).where(PracticeQuestion.session_id == session_id)
    )
    questions_map = {q.question_no: q for q in questions_result.scalars().all()}

    correct_count = 0
    total_count = len(req.results)

    for result in req.results:
        q = questions_map.get(result.question_no)
        if q:
            q.student_answer = result.student_answer
            q.is_correct = result.is_correct
            q.parent_marked = True
            if result.is_correct:
                correct_count += 1

    session.correct_rate = correct_count / total_count if total_count > 0 else 0
    await db.flush()

    return APIResponse(
        data=PracticeSubmitResponse(
            session_id=str(session.id),
            correct_rate=session.correct_rate,
            assessment_status="assessing",
            message="正在评估掌握程度...",
        )
    )


@router.get("/{session_id}/assessment", response_model=APIResponse[PracticeAssessmentResponse])
async def get_assessment(
    session_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取掌握度评估。"""
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

    if session.correct_rate is None:
        raise BadRequestException("尚未提交做题结果")

    # Get practice history for this weakness
    history_result = await db.execute(
        select(PracticeSession)
        .where(
            PracticeSession.weakness_id == weakness.id,
            PracticeSession.correct_rate.isnot(None),
        )
        .order_by(PracticeSession.created_at)
    )
    history_sessions = history_result.scalars().all()

    history = [
        HistoryItem(
            date=s.created_at.strftime("%Y-%m-%d"),
            correct_rate=s.correct_rate or 0,
            mastery_score=weakness.mastery_score,
        )
        for s in history_sessions
    ]

    # Get wrong question details for AI assessment
    wrong_questions_result = await db.execute(
        select(PracticeQuestion)
        .where(PracticeQuestion.session_id == session_id, PracticeQuestion.is_correct == False)
    )
    wrong_questions = wrong_questions_result.scalars().all()

    wrong_details = [
        {"question_no": q.question_no, "question_content": q.question_content, "student_answer": q.student_answer}
        for q in wrong_questions
    ]

    # Call AI for assessment
    try:
        assessment = await ai_service.assess_mastery(
            student_name=student.name,
            grade=student.grade.value,
            knowledge_point=kp.name,
            practice_history=[{"date": h.date, "correct_rate": h.correct_rate} for h in history],
            correct_count=int(session.correct_rate * session.question_count),
            total_count=session.question_count,
            wrong_details=wrong_details,
            db=db,
            user_id=str(current_user.id),
        )

        # Update weakness
        weakness.mastery_score = assessment.get("mastery_score", 0)
        weakness.recommended_days = assessment.get("suggested_days", 2)

        # L-5 fix: use enum member instead of string
        if assessment.get("recommendation") == "mastered":
            weakness.status = WeaknessStatus.MASTERED
            weakness.mastered_at = datetime.now(timezone.utc)

        session.ai_assessment = assessment
        await db.flush()

    except Exception as e:
        logger.error(f"Assessment failed for session {session_id}: {e}")
        # Provide fallback assessment
        assessment = {
            "mastery_score": int(session.correct_rate * 100),
            "trend": "stable",
            "error_pattern": "其他",
            "recommendation": "continue" if session.correct_rate < 0.8 else "mastered",
            "suggested_days": 2 if session.correct_rate < 0.8 else 0,
            "suggestion_detail": "请继续练习以巩固知识",
        }

    return APIResponse(
        data=PracticeAssessmentResponse(
            session_id=str(session.id),
            mastery_score=assessment.get("mastery_score", 0),
            trend=assessment.get("trend", "stable"),
            error_pattern=assessment.get("error_pattern", ""),
            recommendation=assessment.get("recommendation", "continue"),
            suggested_days=assessment.get("suggested_days", 2),
            suggestion_detail=assessment.get("suggestion_detail", ""),
            history=history,
        )
    )
