"""Exam API endpoints: upload, recognition, confirm, analysis."""

import os
import uuid
import logging

from fastapi import APIRouter, Depends, UploadFile, File, Form, BackgroundTasks
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db, async_session_factory
from app.core.config import settings
from app.core.exceptions import NotFoundException, ForbiddenException, BadRequestException
from app.models.user import User, Student
from app.models.exam import Exam, ExamQuestion, ExamStatus
from app.models.knowledge import KnowledgePoint
from app.models.weakness import Weakness, WeaknessStatus
from app.schemas.common import APIResponse
from app.schemas.exam import (
    ExamUploadResponse,
    ExamRecognitionResponse,
    ExamQuestionResponse,
    ExamConfirmRequest,
    ExamConfirmResponse,
    ExamAnalysisResponse,
    WeaknessItem,
)
from app.api.deps import get_current_user
from app.services.ocr_service import ocr_service
from app.services.ai_service import ai_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/exams", tags=["试卷"])


async def _verify_student_ownership(db: AsyncSession, user: User, student_id: uuid.UUID) -> Student:
    result = await db.execute(select(Student).where(Student.id == student_id))
    student = result.scalar_one_or_none()
    if student is None:
        raise NotFoundException("孩子档案不存在")
    if student.user_id != user.id:
        raise ForbiddenException("无权操作该孩子的数据")
    return student


async def _verify_exam_ownership(db: AsyncSession, user: User, exam_id: uuid.UUID) -> Exam:
    result = await db.execute(
        select(Exam).join(Student).where(Exam.id == exam_id, Student.user_id == user.id)
    )
    exam = result.scalar_one_or_none()
    if exam is None:
        raise NotFoundException("试卷不存在")
    return exam


# ─── 后台任务 ─────────────────────────────────────────────────


async def _run_ocr_background(exam_id: str, image_urls: list[str], subject: str):
    """后台执行 OCR 识别，完成后更新 exam 状态和题目。"""
    async with async_session_factory() as db:
        try:
            exam = await db.get(Exam, uuid.UUID(exam_id))
            if not exam:
                logger.error(f"Exam {exam_id} not found for OCR background task")
                return

            result = await ocr_service.recognize_exam(image_urls, subject=subject)
            exam.ai_raw_result = result

            for q_data in result.get("questions", []):
                question = ExamQuestion(
                    exam_id=exam.id,
                    question_no=q_data["question_no"],
                    question_content=q_data.get("question_content", ""),
                    is_correct=q_data.get("is_correct"),
                    score_got=q_data.get("score_got", 0),
                    score_total=q_data.get("score_total", 0),
                    confidence=q_data.get("confidence", 0),
                )
                db.add(question)

            exam.status = ExamStatus.RECOGNIZED
            await db.commit()
            logger.info(f"OCR background: exam {exam_id} recognized ({len(result.get('questions', []))} questions)")

        except Exception as e:
            logger.error(f"OCR background failed for exam {exam_id}: {e}")
            try:
                exam = await db.get(Exam, uuid.UUID(exam_id))
                if exam:
                    exam.status = ExamStatus.UPLOADING
                    await db.commit()
            except Exception:
                pass


async def _run_analysis_background(exam_id: str):
    """后台执行薄弱点分析。"""
    async with async_session_factory() as db:
        try:
            exam = await db.get(Exam, uuid.UUID(exam_id))
            if not exam:
                return

            # Get wrong questions
            questions_result = await db.execute(
                select(ExamQuestion).where(ExamQuestion.exam_id == exam.id)
            )
            questions_map = {q.question_no: q for q in questions_result.scalars().all()}

            wrong_questions = [
                {"question_no": q.question_no, "question_content": q.question_content, "score_got": q.score_got, "score_total": q.score_total}
                for q in questions_map.values() if not q.is_correct
            ]

            result = await ai_service.analyze_weaknesses(
                student_id=str(exam.student_id), subject=exam.subject,
                total_score=exam.total_score, actual_score=exam.actual_score or 0,
                wrong_questions=wrong_questions, db=db,
            )

            for weakness_data in result:
                kp_result = await db.execute(
                    select(KnowledgePoint).where(KnowledgePoint.name == weakness_data["knowledge_point"], KnowledgePoint.subject == exam.subject)
                )
                kp = kp_result.scalar_one_or_none()
                if kp is None:
                    kp = KnowledgePoint(subject=exam.subject, name=weakness_data["knowledge_point"])
                    db.add(kp)
                    await db.flush()

                existing = await db.execute(
                    select(Weakness).where(Weakness.student_id == exam.student_id, Weakness.knowledge_point_id == kp.id)
                )
                weakness = existing.scalar_one_or_none()
                if weakness:
                    if weakness_data["star_rating"] > weakness.star_rating:
                        weakness.star_rating = weakness_data["star_rating"]
                        weakness.reason = weakness_data.get("reason", "")
                else:
                    weakness = Weakness(student_id=exam.student_id, knowledge_point_id=kp.id,
                        star_rating=weakness_data["star_rating"], reason=weakness_data.get("reason", ""),
                        status=WeaknessStatus.NOT_STARTED)
                    db.add(weakness)

            exam.status = ExamStatus.ANALYZED
            await db.commit()
            logger.info(f"Analysis background: exam {exam_id} completed ({len(result)} weaknesses)")

        except Exception as e:
            logger.error(f"Analysis background failed for exam {exam_id}: {e}")
            try:
                exam = await db.get(Exam, uuid.UUID(exam_id))
                if exam:
                    exam.status = ExamStatus.CONFIRMED
                    await db.commit()
            except Exception:
                pass


# ─── 端点 ────────────────────────────────────────────────────


@router.post("/upload", response_model=APIResponse[ExamUploadResponse])
async def upload_exam(
    student_id: uuid.UUID = Form(...),
    subject: str = Form(...),
    exam_name: str = Form(None),
    total_score: int = Form(...),
    actual_score: int = Form(None),
    images: list[UploadFile] = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """上传试卷照片（直接上传文件模式，保留向后兼容）。"""
    await _verify_student_ownership(db, current_user, student_id)
    valid_subjects = ["math", "politics", "history"]
    if subject not in valid_subjects:
        raise BadRequestException(f"不支持的学科：{subject}")
    if not images or len(images) > 5:
        raise BadRequestException("请上传 1-5 张试卷照片")

    ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "bmp", "webp"}
    MAX_FILE_SIZE = 10 * 1024 * 1024
    image_urls = []
    upload_dir = os.path.join(settings.UPLOAD_DIR, str(student_id))
    os.makedirs(upload_dir, exist_ok=True)

    for img in images:
        if not img.content_type or not img.content_type.startswith("image/"):
            raise BadRequestException("只能上传图片文件")
        raw_ext = img.filename.split(".")[-1].lower() if img.filename else "jpg"
        if raw_ext not in ALLOWED_EXTENSIONS:
            raise BadRequestException(f"不支持的图片格式：{raw_ext}")
        content = await img.read()
        if len(content) > MAX_FILE_SIZE:
            raise BadRequestException("图片大小超过限制（最大 10MB）")
        filename = f"{uuid.uuid4().hex}.{raw_ext}"
        filepath = os.path.join(upload_dir, filename)
        with open(filepath, "wb") as f:
            f.write(content)
        image_urls.append(filepath)

    exam = Exam(student_id=student_id, subject=subject, exam_name=exam_name,
        total_score=total_score, actual_score=actual_score, image_urls=image_urls,
        status=ExamStatus.RECOGNIZING)
    db.add(exam)
    await db.flush()

    # 同步执行 OCR（直接上传模式向后兼容）
    try:
        recognition_result = await ocr_service.recognize_exam(image_urls, subject=subject)
        exam.ai_raw_result = recognition_result
        for q_data in recognition_result.get("questions", []):
            db.add(ExamQuestion(exam_id=exam.id, question_no=q_data["question_no"],
                question_content=q_data.get("question_content", ""), is_correct=q_data.get("is_correct"),
                score_got=q_data.get("score_got", 0), score_total=q_data.get("score_total", 0),
                confidence=q_data.get("confidence", 0)))
        exam.status = ExamStatus.RECOGNIZED
        await db.flush()
        logger.info(f"Exam {exam.id} recognized ({len(recognition_result.get('questions', []))} questions)")
    except Exception as e:
        logger.error(f"OCR failed for exam {exam.id}: {e}")
        exam.status = ExamStatus.UPLOADING
        await db.flush()
        return APIResponse(code=1, message="识别失败，请重新上传",
            data=ExamUploadResponse(exam_id=str(exam.id), status=exam.status.value, message="识别失败"))

    return APIResponse(data=ExamUploadResponse(exam_id=str(exam.id), status=exam.status.value, message="识别完成"))


@router.post("/upload-image")
async def upload_single_image(
    image: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    """上传单张图片，返回图片 URL。"""
    ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "bmp", "webp"}
    MAX_FILE_SIZE = 10 * 1024 * 1024
    if not image.content_type or not image.content_type.startswith("image/"):
        raise BadRequestException("只能上传图片文件")
    raw_ext = image.filename.split(".")[-1].lower() if image.filename else "jpg"
    if raw_ext not in ALLOWED_EXTENSIONS:
        raise BadRequestException(f"不支持的图片格式：{raw_ext}")
    content = await image.read()
    if len(content) > MAX_FILE_SIZE:
        raise BadRequestException("图片大小超过限制（最大 10MB）")
    upload_dir = os.path.join(settings.UPLOAD_DIR, str(current_user.id))
    os.makedirs(upload_dir, exist_ok=True)
    filename = f"{uuid.uuid4().hex}.{raw_ext}"
    filepath = os.path.join(upload_dir, filename)
    with open(filepath, "wb") as f:
        f.write(content)
    logger.info(f"Image uploaded: {filepath}")
    return APIResponse(data={"url": filepath, "filename": filename})


@router.post("/upload-by-urls", response_model=APIResponse[ExamUploadResponse])
async def upload_exam_by_urls(
    body: dict,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    上传试卷（URL 方式）→ 立即返回 recognizing → 后台 OCR。
    前端轮询 GET /exams/{id}/recognition 直到 status=recognized。
    """
    student_id = uuid.UUID(body.get("student_id"))
    subject = body.get("subject")
    if not subject: raise BadRequestException("subject 不能为空")
    if subject not in ("math", "politics", "history"):
        raise BadRequestException(f"不支持的学科：{subject}")
    await _verify_student_ownership(db, current_user, student_id)

    image_urls = body.get("image_urls", [])
    if not image_urls:
        raise BadRequestException("image_urls 不能为空")
    if len(image_urls) > 5:
        raise BadRequestException("最多上传 5 张图片")

    exam = Exam(student_id=student_id, subject=subject, exam_name=body.get("exam_name"),
        total_score=body.get("total_score"), actual_score=body.get("actual_score"),
        image_urls=image_urls, status=ExamStatus.RECOGNIZING)
    db.add(exam)
    await db.flush()

    background_tasks.add_task(_run_ocr_background, str(exam.id), image_urls, subject)
    logger.info(f"Exam {exam.id} created, OCR background")

    return APIResponse(data=ExamUploadResponse(exam_id=str(exam.id),
        status=ExamStatus.RECOGNIZING.value, message="试卷已接收，正在识别中"))


@router.get("/{exam_id}/recognition")
async def get_recognition(
    exam_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取识别结果（供前端轮询）。status=recognized 时 questions 有数据。"""
    exam = await _verify_exam_ownership(db, current_user, exam_id)
    result = await db.execute(
        select(ExamQuestion).where(ExamQuestion.exam_id == exam_id).order_by(ExamQuestion.question_no)
    )
    questions = result.scalars().all()
    return APIResponse(data={
        "exam_id": str(exam.id),
        "status": exam.status.value,
        "questions": [ExamQuestionResponse.model_validate(q) for q in questions],
        "message": "正在识别中" if exam.status == ExamStatus.RECOGNIZING else "识别完成",
    })


@router.post("/{exam_id}/confirm", response_model=APIResponse[ExamConfirmResponse])
async def confirm_recognition(
    exam_id: uuid.UUID,
    req: ExamConfirmRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    家长确认识别结果 → status=analyzing → 后台分析。
    前端轮询 GET /exams/{id}/analysis 直到 status=analyzed。
    """
    exam = await _verify_exam_ownership(db, current_user, exam_id)
    if exam.status not in (ExamStatus.RECOGNIZED, ExamStatus.CONFIRMED, ExamStatus.ANALYZED):
        raise BadRequestException("当前试卷状态不允许确认")

    result = await db.execute(select(ExamQuestion).where(ExamQuestion.exam_id == exam_id))
    questions_map = {q.question_no: q for q in result.scalars().all()}
    for c in req.questions:
        q = questions_map.get(c.question_no)
        if q:
            q.is_correct = c.is_correct
            q.score_got = c.score_got
            q.student_answer = c.student_answer
            q.parent_verified = c.parent_verified

    exam.status = ExamStatus.ANALYZING
    await db.flush()
    await db.commit()

    background_tasks.add_task(_run_analysis_background, str(exam_id))
    logger.info(f"Exam {exam.id} confirmed, analysis background")

    return APIResponse(data=ExamConfirmResponse(exam_id=str(exam.id), status=ExamStatus.ANALYZING.value),
        message="已确认，AI 正在分析薄弱点")


@router.get("/{exam_id}/analysis")
async def get_analysis(
    exam_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取薄弱点分析结果（供前端轮询）。
    - analyzing: 分析中，weaknesses 为空
    - analyzed: 完成，weaknesses 有数据
    """
    exam = await _verify_exam_ownership(db, current_user, exam_id)

    if exam.status == ExamStatus.ANALYZING:
        return APIResponse(data=ExamAnalysisResponse(
            exam_id=str(exam.id), subject=exam.subject,
            total_score=exam.total_score, actual_score=exam.actual_score,
            weaknesses=[]),
            message="AI 正在分析中")

    if exam.status == ExamStatus.ANALYZED:
        weaknesses_result = await db.execute(
            select(Weakness, KnowledgePoint).join(KnowledgePoint, Weakness.knowledge_point_id == KnowledgePoint.id)
            .where(Weakness.student_id == exam.student_id, KnowledgePoint.subject == exam.subject)
            .order_by(Weakness.star_rating.desc())
        )
        return APIResponse(data=ExamAnalysisResponse(
            exam_id=str(exam.id), subject=exam.subject,
            total_score=exam.total_score, actual_score=exam.actual_score,
            weaknesses=[WeaknessItem(weakness_id=str(w.id), knowledge_point=kp.name,
                star_rating=w.star_rating, reason=w.reason or "", status=w.status.value)
                for w, kp in weaknesses_result.all()]))

    raise BadRequestException("分析未完成或尚未开始")
