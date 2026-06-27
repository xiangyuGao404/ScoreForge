"""Weakness ORM model."""

import uuid
from datetime import datetime, timezone
from enum import Enum as PyEnum

from sqlalchemy import String, DateTime, ForeignKey, Enum, Text, Integer, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class WeaknessStatus(str, PyEnum):
    NOT_STARTED = "not_started"
    PRACTICING = "practicing"
    MASTERED = "mastered"


class Weakness(Base):
    __tablename__ = "weaknesses"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("students.id", ondelete="CASCADE"), index=True)
    knowledge_point_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("knowledge_points.id"), index=True)
    star_rating: Mapped[int] = mapped_column(Integer)  # 1-5
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[WeaknessStatus] = mapped_column(Enum(WeaknessStatus), default=WeaknessStatus.NOT_STARTED)
    mastery_score: Mapped[float] = mapped_column(Float, default=0)
    practice_days: Mapped[int] = mapped_column(Integer, default=0)
    recommended_days: Mapped[int] = mapped_column(Integer, default=0)
    mastered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    # Relationships
    student: Mapped["Student"] = relationship(back_populates="weaknesses")
    knowledge_point: Mapped["KnowledgePoint"] = relationship()
