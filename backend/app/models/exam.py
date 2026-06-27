"""Exam and ExamQuestion ORM models."""

import uuid
from datetime import datetime, timezone
from enum import Enum as PyEnum

from sqlalchemy import String, DateTime, ForeignKey, Enum, Text, Integer, Float, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ExamStatus(str, PyEnum):
    UPLOADING = "uploading"
    RECOGNIZING = "recognizing"
    RECOGNIZED = "recognized"
    CONFIRMED = "confirmed"
    ANALYZING = "analyzing"
    ANALYZED = "analyzed"


class Exam(Base):
    __tablename__ = "exams"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("students.id", ondelete="CASCADE"), index=True)
    subject: Mapped[str] = mapped_column(String(20))  # math, politics, history
    exam_name: Mapped[str | None] = mapped_column(String(50), nullable=True)
    total_score: Mapped[int] = mapped_column(Integer)
    actual_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    image_urls: Mapped[list] = mapped_column(JSONB, default=list)
    status: Mapped[ExamStatus] = mapped_column(Enum(ExamStatus), default=ExamStatus.UPLOADING)
    ai_raw_result: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    # Relationships
    student: Mapped["Student"] = relationship(back_populates="exams")
    questions: Mapped[list["ExamQuestion"]] = relationship(back_populates="exam", cascade="all, delete-orphan")


class ExamQuestion(Base):
    __tablename__ = "exam_questions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    exam_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("exams.id", ondelete="CASCADE"), index=True)
    question_no: Mapped[int] = mapped_column(Integer)
    question_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    correct_answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    student_answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_correct: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    score_got: Mapped[float] = mapped_column(Float, default=0)
    score_total: Mapped[float] = mapped_column(Float, default=0)
    confidence: Mapped[float] = mapped_column(Float, default=0)
    knowledge_point_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("knowledge_points.id"), nullable=True)
    parent_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    # Relationships
    exam: Mapped["Exam"] = relationship(back_populates="questions")
