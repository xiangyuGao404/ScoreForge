"""Practice request/response schemas."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class PracticeGenerateRequest(BaseModel):
    student_id: str
    weakness_id: str
    mode: str = "online"
    question_count: int = 5


class PracticeGenerateResponse(BaseModel):
    session_id: str
    mode: str
    status: str
    message: str


class PracticeQuestionResponse(BaseModel):
    question_no: int
    difficulty: str
    question_content: str
    question_type: str
    reference_answer: str
    solution_detail: str

    model_config = {"from_attributes": True}


class PracticeQuestionsResponse(BaseModel):
    session_id: str
    weakness: str
    questions: list[PracticeQuestionResponse]


class SubmitResult(BaseModel):
    question_no: int
    student_answer: str
    is_correct: bool


class PracticeSubmitRequest(BaseModel):
    results: list[SubmitResult]


class PracticeSubmitResponse(BaseModel):
    session_id: str
    correct_rate: float
    assessment_status: str
    message: str


class HistoryItem(BaseModel):
    date: str
    correct_rate: float
    mastery_score: float


class PracticeAssessmentResponse(BaseModel):
    session_id: str
    mastery_score: int
    trend: str
    error_pattern: str
    recommendation: str
    suggested_days: int
    suggestion_detail: str
    history: list[HistoryItem]
