"""Student request/response schemas."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


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


class StudentListResponse(BaseModel):
    students: list[StudentResponse]
