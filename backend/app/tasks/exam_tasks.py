"""Async tasks for exam processing."""

import asyncio
import logging
import uuid

from app.celery_app import celery
from app.core.database import async_session_factory
from app.models.exam import Exam, ExamQuestion, ExamStatus

logger = logging.getLogger(__name__)


@celery.task(bind=True, max_retries=3)
def recognize_exam_task(self, exam_id: str):
    """Async task to recognize exam paper using OCR."""
    try:
        asyncio.run(_recognize_exam(exam_id))
    except Exception as exc:
        logger.error(f"OCR task failed for exam {exam_id}: {exc}")
        self.retry(exc=exc, countdown=30)


async def _recognize_exam(exam_id: str):
    """Run OCR recognition asynchronously."""
    from app.services.ocr_service import ocr_service

    async with async_session_factory() as db:
        from sqlalchemy import select

        result = await db.execute(select(Exam).where(Exam.id == uuid.UUID(exam_id)))
        exam = result.scalar_one_or_none()

        if not exam:
            logger.error(f"Exam {exam_id} not found")
            return

        try:
            recognition_result = await ocr_service.recognize_exam(exam.image_urls)
            exam.ai_raw_result = recognition_result

            # Create exam questions
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
            await db.commit()
            logger.info(f"Exam {exam_id} recognized successfully")

        except Exception as e:
            logger.error(f"OCR recognition failed for exam {exam_id}: {e}")
            exam.status = ExamStatus.UPLOADING
            await db.commit()
