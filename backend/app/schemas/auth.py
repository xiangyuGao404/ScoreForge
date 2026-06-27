"""Auth request/response schemas."""

from pydantic import BaseModel


class SendCodeRequest(BaseModel):
    phone: str


class LoginRequest(BaseModel):
    phone: str
    code: str


class LoginResponse(BaseModel):
    token: str
    user_id: str
    nickname: str
    user_level: str
