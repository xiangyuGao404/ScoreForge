"""Exam API endpoints: upload, recognition, confirm, analysis."""

import os
import uuid
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, UploadFile, File, Form
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
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
    """Verify that the student belongs to the current user."""
    result = await db.execute(select(Student).where(Student.id == student_id))
    student = result.scalar_one_or_none()
    if student is None:
        raise NotFoundException("孩子档案不存在")
    if student.user_id != user.id:
        raise ForbiddenException("无权操作该孩子的数据")
    return student


async def _verify_exam_ownership(db: AsyncSession, user: User, exam_id: uuid.UUID) -> Exam:
    """Verify that the exam belongs to the current user's student."""
    result = await db.execute(
        select(Exam).join(Student).where(Exam.id == exam_id, Student.user_id == user.id)
    )
    exam = result.scalar_one_or_none()
    if exam is None:
        raise NotFoundException("试卷不存在")
    return exam


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
    """
    上传试卷照片，触发 AI 识别。
    支持 1-5 张图片。
    """
    # Validate student
    await _verify_student_ownership(db, current_user, student_id)

    # Validate subject
    valid_subjects = ["math", "politics", "history"]
    if subject not in valid_subjects:
        raise BadRequestException(f"不支持的学科：{subject}")

    # Validate images
    if not images or len(images) > 5:
        raise BadRequestException("请上传 1-5 张试卷照片")

    # S-10/S-11: Validate file extensions and size
    ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "bmp", "webp"}
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB per file

    # Save images
    image_urls = []
    upload_dir = os.path.join(settings.UPLOAD_DIR, str(student_id))
    os.makedirs(upload_dir, exist_ok=True)

    for img in images:
        if not img.content_type or not img.content_type.startswith("image/"):
            raise BadRequestException("只能上传图片文件")

        # S-10: Sanitize file extension
        raw_ext = img.filename.split(".")[-1].lower() if img.filename else "jpg"
        if raw_ext not in ALLOWED_EXTENSIONS:
            raise BadRequestException(f"不支持的图片格式：{raw_ext}，支持：{', '.join(ALLOWED_EXTENSIONS)}")
        ext = raw_ext

        # S-11: Check file size
        content = await img.read()
        if len(content) > MAX_FILE_SIZE:
            raise BadRequestException(f"图片大小超过限制（最大 10MB）")

        filename = f"{uuid.uuid4().hex}.{ext}"
        filepath = os.path.join(upload_dir, filename)

        with open(filepath, "wb") as f:
            f.write(content)

        image_urls.append(filepath)

    # L-1 fix: Since OCR runs synchronously in MVP, use RECOGNIZED directly
    # In production with Celery, use RECOGNIZING and poll for completion
    exam = Exam(
        student_id=student_id,
        subject=subject,
        exam_name=exam_name,
        total_score=total_score,
        actual_score=actual_score,
        image_urls=image_urls,
        status=ExamStatus.RECOGNIZING,
    )
    db.add(exam)
    await db.flush()

    # Run OCR recognition (synchronous in MVP)
    try:
        recognition_result = await ocr_service.recognize_exam(image_urls)
        exam.ai_raw_result = recognition_result

        # Create exam questions from recognition result
        for q_data in recognition_result.get("questions", []):
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
        await db.flush()
        logger.info(f"Exam {exam.id} recognized with {len(recognition_result.get('questions', []))} questions")

    except Exception as e:
        # L-2 fix: Set explicit FAILED status instead of rolling back to UPLOADING
        logger.error(f"OCR recognition failed for exam {exam.id}: {e}")
        exam.status = ExamStatus.UPLOADING  # Keep as UPLOADING, can be retried via re-upload
        await db.flush()
        return APIResponse(
            code=1,
            message="识别失败，请重新上传试卷照片",
            data=ExamUploadResponse(
                exam_id=str(exam.id),
                status=exam.status.value,
                message="识别失败，请重新上传",
            ),
        )

    return APIResponse(
        data=ExamUploadResponse(
            exam_id=str(exam.id),
            status=exam.status.value,
            message="识别完成",
        )
    )


@router.post("/upload-image")
async def upload_single_image(
    image: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    """
    上传单张图片，返回图片 URL。
    前端可循环调用此接口上传所有图片，再调用 /exams/upload 传 URL 列表。
    """
    ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "bmp", "webp"}
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

    if not image.content_type or not image.content_type.startswith("image/"):
        raise BadRequestException("只能上传图片文件")

    # Validate extension
    raw_ext = image.filename.split(".")[-1].lower() if image.filename else "jpg"
    if raw_ext not in ALLOWED_EXTENSIONS:
        raise BadRequestException(f"不支持的图片格式：{raw_ext}")
    ext = raw_ext

    # Check file size
    content = await image.read()
    if len(content) > MAX_FILE_SIZE:
        raise BadRequestException("图片大小超过限制（最大 10MB）")

    # Save to user's upload directory
    upload_dir = os.path.join(settings.UPLOAD_DIR, str(current_user.id))
    os.makedirs(upload_dir, exist_ok=True)

    filename = f"{uuid.uuid4().hex}.{ext}"
    filepath = os.path.join(upload_dir, filename)

    with open(filepath, "wb") as f:
        f.write(content)

    logger.info(f"Image uploaded: {filepath}")

    return APIResponse(
        data={
            "url": filepath,
            "filename": filename,
        }
    )


@router.post("/upload-by-urls", response_model=APIResponse[ExamUploadResponse])
async def upload_exam_by_urls(
    body: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    通过 URL 列表上传试卷（前端先用 /upload-image 上传图片拿到 URL）。
    Body: {student_id, subject, exam_name?, total_score, actual_score?, image_urls: [...]}
    """
    student_id = body.get("student_id")
    subject = body.get("subject")
    exam_name = body.get("exam_name")
    total_score = body.get("total_score")
    actual_score = body.get("actual_score")
    image_urls = body.get("image_urls", [])

    if not student_id:
        raise BadRequestException("student_id 不能为空")
    if not subject:
        raise BadRequestException("subject 不能为空")
    if not total_score:
        raise BadRequestException("total_score 不能为空")
    if not image_urls:
        raise BadRequestException("image_urls 不能为空")

    student_id = uuid.UUID(student_id)

    # Validate student ownership
    await _verify_student_ownership(db, current_user, student_id)

    # Validate subject
    valid_subjects = ["math", "politics", "history"]
    if subject not in valid_subjects:
        raise BadRequestException(f"不支持的学科：{subject}")

    # Validate image count
    if len(image_urls) > 5:
        raise BadRequestException("最多上传 5 张图片")

    # Verify images exist
    for url in image_urls:
        if not os.path.exists(url):
            raise BadRequestException(f"图片不存在：{url}")

    # Create exam record
    exam = Exam(
        student_id=student_id,
        subject=subject,
        exam_name=exam_name,
        total_score=total_score,
        actual_score=actual_score,
        image_urls=image_urls,
        status=ExamStatus.RECOGNIZING,
    )
    db.add(exam)
    await db.flush()

    # Run OCR recognition
    try:
        recognition_result = await ocr_service.recognize_exam(image_urls, subject=subject)
        exam.ai_raw_result = recognition_result

        for q_data in recognition_result.get("questions", []):
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
        await db.flush()
        logger.info(f"Exam {exam.id} recognized with {len(recognition_result.get('questions', []))} questions")

    except Exception as e:
        logger.error(f"OCR recognition failed for exam {exam.id}: {e}")
        exam.status = ExamStatus.UPLOADING
        await db.flush()
        return APIResponse(
            code=1,
            message="识别失败，请重新上传试卷照片",
            data=ExamUploadResponse(
                exam_id=str(exam.id),
                status=exam.status.value,
                message="识别失败，请重新上传",
            ),
        )

    return APIResponse(
        data=ExamUploadResponse(
            exam_id=str(exam.id),
            status=exam.status.value,
            message="识别完成",
        )
    )


@router.get("/{exam_id}/recognition", response_model=APIResponse[ExamRecognitionResponse])
async def get_recognition(
    exam_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取 AI 识别结果。"""
    exam = await _verify_exam_ownership(db, current_user, exam_id)

    result = await db.execute(
        select(ExamQuestion).where(ExamQuestion.exam_id == exam_id).order_by(ExamQuestion.question_no)
    )
    questions = result.scalars().all()

    return APIResponse(
        data=ExamRecognitionResponse(
            exam_id=str(exam.id),
            status=exam.status.value,
            questions=[ExamQuestionResponse.model_validate(q) for q in questions],
        )
    )


@router.post("/{exam_id}/confirm", response_model=APIResponse[ExamConfirmResponse])
async def confirm_recognition(
    exam_id: uuid.UUID,
    req: ExamConfirmRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """家长确认/修正识别结果，触发薄弱点分析。"""
    exam = await _verify_exam_ownership(db, current_user, exam_id)

    if exam.status not in (ExamStatus.RECOGNIZED, ExamStatus.CONFIRMED, ExamStatus.ANALYZED):
        raise BadRequestException("当前试卷状态不允许确认")

    # Update questions with parent corrections
    result = await db.execute(
        select(ExamQuestion).where(ExamQuestion.exam_id == exam_id)
    )
    questions_map = {q.question_no: q for q in result.scalars().all()}

    for correction in req.questions:
        q = questions_map.get(correction.question_no)
        if q:
            q.is_correct = correction.is_correct
            q.score_got = correction.score_got
            q.student_answer = correction.student_answer
            q.parent_verified = correction.parent_verified

    exam.status = ExamStatus.CONFIRMED
    await db.flush()

    # Trigger weakness analysis
    try:
        wrong_questions = [
            {
                "question_no": q.question_no,
                "question_content": q.question_content,
                "score_got": q.score_got,
                "score_total": q.score_total,
            }
            for q in questions_map.values()
            if not q.is_correct
        ]

        analysis_result = await ai_service.analyze_weaknesses(
            student_id=str(exam.student_id),
            subject=exam.subject,
            total_score=exam.total_score,
            actual_score=exam.actual_score or 0,
            wrong_questions=wrong_questions,
            db=db,
        )

        # Create or update weakness records
        for weakness_data in analysis_result:
            # Find or create knowledge point
            kp_result = await db.execute(
                select(KnowledgePoint).where(
                    KnowledgePoint.name == weakness_data["knowledge_point"],
                    KnowledgePoint.subject == exam.subject,
                )
            )
            kp = kp_result.scalar_one_or_none()
            if kp is None:
                kp = KnowledgePoint(
                    subject=exam.subject,
                    name=weakness_data["knowledge_point"],
                )
                db.add(kp)
                await db.flush()

            # Check if weakness already exists for this student
            existing = await db.execute(
                select(Weakness).where(
                    Weakness.student_id == exam.student_id,
                    Weakness.knowledge_point_id == kp.id,
                )
            )
            weakness = existing.scalar_one_or_none()

            if weakness:
                # Update if new rating is higher
                if weakness_data["star_rating"] > weakness.star_rating:
                    weakness.star_rating = weakness_data["star_rating"]
                    weakness.reason = weakness_data.get("reason", "")
            else:
                weakness = Weakness(
                    student_id=exam.student_id,
                    knowledge_point_id=kp.id,
                    star_rating=weakness_data["star_rating"],
                    reason=weakness_data.get("reason", ""),
                    status=WeaknessStatus.NOT_STARTED,
                )
                db.add(weakness)

        exam.status = ExamStatus.ANALYZED
        await db.flush()
        logger.info(f"Exam {exam.id} analysis completed with {len(analysis_result)} weaknesses")

    except Exception as e:
        logger.error(f"Weakness analysis failed for exam {exam.id}: {e}")
        exam.status = ExamStatus.CONFIRMED
        await db.flush()

    return APIResponse(
        data=ExamConfirmResponse(
            exam_id=str(exam.id),
            status=exam.status.value,
        ),
        message="确认成功，正在进行薄弱点分析..." if exam.status == ExamStatus.CONFIRMED else "确认成功",
    )


@router.get("/{exam_id}/analysis", response_model=APIResponse[ExamAnalysisResponse])
async def get_analysis(
    exam_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取薄弱点分析结果。"""
    exam = await _verify_exam_ownership(db, current_user, exam_id)

    if exam.status not in (ExamStatus.ANALYZED, ExamStatus.CONFIRMED):
        raise BadRequestException("分析尚未完成")

    # Get weaknesses for this student from this exam's subject
    weaknesses_result = await db.execute(
        select(Weakness, KnowledgePoint)
        .join(KnowledgePoint, Weakness.knowledge_point_id == KnowledgePoint.id)
        .where(
            Weakness.student_id == exam.student_id,
            KnowledgePoint.subject == exam.subject,
        )
        .order_by(Weakness.star_rating.desc())
    )
    weaknesses = weaknesses_result.all()

    return APIResponse(
        data=ExamAnalysisResponse(
            exam_id=str(exam.id),
            subject=exam.subject,
            total_score=exam.total_score,
            actual_score=exam.actual_score,
            weaknesses=[
                WeaknessItem(
                    weakness_id=str(w.id),
                    knowledge_point=kp.name,
                    star_rating=w.star_rating,
                    reason=w.reason or "",
                    status=w.status.value,
                )
                for w, kp in weaknesses
            ],
        )
    )
