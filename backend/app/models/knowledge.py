"""KnowledgePoint ORM model."""

import uuid

from sqlalchemy import String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class KnowledgePoint(Base):
    __tablename__ = "knowledge_points"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    subject: Mapped[str] = mapped_column(String(20), index=True)
    name: Mapped[str] = mapped_column(String(100), index=True)
    parent_path: Mapped[str | None] = mapped_column(String(255), nullable=True)  # e.g. "数学>函数>一次函数"
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
