"""PracticeSession and PracticeQuestion ORM models."""

import uuid
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import String, DateTime, ForeignKey, Enum, Text, Integer, Float, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.utils import utcnow


class PracticeMode(str, PyEnum):
    ONLINE = "online"
    PDF = "pdf"


class Difficulty(str, PyEnum):
    BASIC = "basic"
    MEDIUM = "medium"
    ADVANCED = "advanced"


class QuestionType(str, PyEnum):
    CHOICE = "choice"
    FILL_BLANK = "fill_blank"
    SOLVE = "solve"


class MasteryStatus(str, PyEnum):
    PRACTICING = "practicing"
    MASTERED = "mastered"


class PracticeStatus(str, PyEnum):
    GENERATING = "generating"
    READY = "ready"
    ASSESSING = "assessing"
    ASSESSED = "assessed"


class PracticeSession(Base):
    __tablename__ = "practice_sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("students.id", ondelete="CASCADE"), index=True)
    weakness_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("weaknesses.id", ondelete="CASCADE"), index=True)
    mode: Mapped[PracticeMode] = mapped_column(Enum(PracticeMode), default=PracticeMode.ONLINE)
    status: Mapped[PracticeStatus] = mapped_column(Enum(PracticeStatus), default=PracticeStatus.GENERATING)
    question_count: Mapped[int] = mapped_column(Integer, default=5)
    correct_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    mastery_status: Mapped[MasteryStatus] = mapped_column(Enum(MasteryStatus), default=MasteryStatus.PRACTICING)
    ai_assessment: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    # Relationships
    student: Mapped["Student"] = relationship(back_populates="practice_sessions")
    questions: Mapped[list["PracticeQuestion"]] = relationship(back_populates="session", cascade="all, delete-orphan")


class PracticeQuestion(Base):
    __tablename__ = "practice_questions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("practice_sessions.id", ondelete="CASCADE"), index=True)
    question_no: Mapped[int] = mapped_column(Integer)
    question_content: Mapped[str] = mapped_column(Text)
    reference_answer: Mapped[str] = mapped_column(Text)
    solution_detail: Mapped[str] = mapped_column(Text)
    difficulty: Mapped[Difficulty] = mapped_column(Enum(Difficulty))
    # DB-7 fix: use enum instead of free string
    question_type: Mapped[QuestionType] = mapped_column(Enum(QuestionType), default=QuestionType.SOLVE)
    student_answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_correct: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    parent_marked: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    # Relationships
    session: Mapped["PracticeSession"] = relationship(back_populates="questions")
