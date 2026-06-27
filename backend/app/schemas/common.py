"""Common response schemas."""

from typing import Any, Generic, TypeVar
from pydantic import BaseModel

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    """Standard API response format."""
    code: int = 0
    message: str = "success"
    data: T | None = None


class ErrorResponse(BaseModel):
    """Standard error response format."""
    code: int
    message: str
    detail: str = ""
