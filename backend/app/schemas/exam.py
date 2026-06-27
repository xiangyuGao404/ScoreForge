"""Exam request/response schemas."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class ExamUploadResponse(BaseModel):
    exam_id: str
    status: str
    message: str


class ExamQuestionResponse(BaseModel):
    question_no: int
    question_content: Optional[str] = None
    is_correct: Optional[bool] = None
    score_got: float = 0
    score_total: float = 0
    confidence: float = 0
    parent_verified: bool = False

    model_config = {"from_attributes": True}


class ExamRecognitionResponse(BaseModel):
    exam_id: str
    status: str
    questions: list[ExamQuestionResponse]


class ConfirmQuestion(BaseModel):
    question_no: int
    is_correct: bool
    score_got: float
    student_answer: Optional[str] = None
    parent_verified: bool = True


class ExamConfirmRequest(BaseModel):
    questions: list[ConfirmQuestion]


class ExamConfirmResponse(BaseModel):
    exam_id: str
    status: str


class WeaknessItem(BaseModel):
    weakness_id: str
    knowledge_point: str
    star_rating: int
    reason: str
    status: str


class ExamAnalysisResponse(BaseModel):
    exam_id: str
    subject: str
    total_score: int
    actual_score: Optional[int] = None
    weaknesses: list[WeaknessItem]
