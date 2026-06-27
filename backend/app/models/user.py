"""User and Student ORM models."""

import uuid
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import String, DateTime, ForeignKey, Enum, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.utils import utcnow


class UserLevel(str, PyEnum):
    FREE = "free"
    PAID = "paid"


class Grade(str, PyEnum):
    GRADE_7 = "初一"
    GRADE_8 = "初二"
    GRADE_9 = "初三"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    phone: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    wechat_openid: Mapped[str | None] = mapped_column(String(128), unique=True, nullable=True)
    nickname: Mapped[str] = mapped_column(String(50), default="家长")
    user_level: Mapped[UserLevel] = mapped_column(Enum(UserLevel), default=UserLevel.FREE)
    api_key_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    # 存储格式：Fernet 加密后的 JSON 字符串
    # {"provider":"xiaomi","api_key":"tp-xxx","api_base":"...","general_model":"...","vision_model":"..."}
    api_config_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    paid_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    # Relationships
    students: Mapped[list["Student"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class Student(Base):
    __tablename__ = "students"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(50))
    grade: Mapped[Grade] = mapped_column(Enum(Grade))
    school: Mapped[str | None] = mapped_column(String(100), nullable=True)
    subjects: Mapped[list] = mapped_column(JSONB, default=list)  # ["math", "politics", "history"]
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="students")
    exams: Mapped[list["Exam"]] = relationship(back_populates="student", cascade="all, delete-orphan")
    weaknesses: Mapped[list["Weakness"]] = relationship(back_populates="student", cascade="all, delete-orphan")
    practice_sessions: Mapped[list["PracticeSession"]] = relationship(back_populates="student", cascade="all, delete-orphan")


# Import here to avoid circular imports
from app.models.exam import Exam  # noqa: E402
from app.models.weakness import Weakness  # noqa: E402
from app.models.practice import PracticeSession  # noqa: E402
