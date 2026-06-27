"""API v1 router."""

from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.students import router as students_router
from app.api.v1.exams import router as exams_router
from app.api.v1.weaknesses import router as weaknesses_router
from app.api.v1.practice import router as practice_router
from app.api.v1.pdf import router as pdf_router
from app.api.v1.chat import router as chat_router
from app.api.v1.settings import router as settings_router

api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(auth_router)
api_v1_router.include_router(students_router)
api_v1_router.include_router(exams_router)
api_v1_router.include_router(weaknesses_router)
api_v1_router.include_router(practice_router)
api_v1_router.include_router(pdf_router)
api_v1_router.include_router(chat_router)
api_v1_router.include_router(settings_router)
