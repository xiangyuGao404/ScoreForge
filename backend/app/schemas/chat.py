"""Chat request/response schemas."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class ChatSendRequest(BaseModel):
    student_id: str
    teacher_role: str  # math, politics, history, homeroom
    content: str


class ChatMessageResponse(BaseModel):
    id: str
    role: str  # user, assistant
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ChatHistoryResponse(BaseModel):
    messages: list[ChatMessageResponse]
