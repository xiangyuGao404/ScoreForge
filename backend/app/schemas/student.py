"""Student request/response schemas."""

import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, field_validator


class StudentCreate(BaseModel):
    name: str
    grade: str
    school: Optional[str] = None
    subjects: list[str] = ["math"]


class StudentUpdate(BaseModel):
    name: Optional[str] = None
    grade: Optional[str] = None
    school: Optional[str] = None
    subjects: Optional[list[str]] = None


class StudentResponse(BaseModel):
    id: str
    name: str
    grade: str
    school: Optional[str] = None
    subjects: list[str] = []
    created_at: datetime

    model_config = {"from_attributes": True}

    @field_validator("id", mode="before")
    @classmethod
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        return v


class StudentListResponse(BaseModel):
    students: list[StudentResponse]
