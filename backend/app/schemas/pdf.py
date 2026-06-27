"""PDF request/response schemas."""

from pydantic import BaseModel


class PDFGenerateRequest(BaseModel):
    session_id: str
    include_answers: bool = True
    include_solutions: bool = True


class PDFGenerateResponse(BaseModel):
    pdf_id: str
    status: str
    message: str
