"""Student management API endpoints."""

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import NotFoundException, ForbiddenException, BadRequestException
from app.models.user import User, Student
from app.schemas.common import APIResponse
from app.schemas.student import StudentCreate, StudentUpdate, StudentResponse, StudentListResponse
from app.api.deps import get_current_user

router = APIRouter(prefix="/students", tags=["学生档案"])


@router.get("", response_model=APIResponse[StudentListResponse])
async def list_students(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取当前用户的孩子列表。"""
    result = await db.execute(
        select(Student).where(Student.user_id == current_user.id).order_by(Student.created_at)
    )
    students = result.scalars().all()

    return APIResponse(
        data=StudentListResponse(
            students=[StudentResponse.model_validate(s) for s in students]
        )
    )


@router.post("", response_model=APIResponse[StudentResponse])
async def create_student(
    req: StudentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """创建孩子档案。"""
    # Validate grade
    valid_grades = ["初一", "初二", "初三"]
    if req.grade not in valid_grades:
        raise BadRequestException(f"年级必须是以下之一：{', '.join(valid_grades)}")

    # Validate subjects
    valid_subjects = ["math", "politics", "history"]
    for subj in req.subjects:
        if subj not in valid_subjects:
            raise BadRequestException(f"不支持的学科：{subj}")

    student = Student(
        user_id=current_user.id,
        name=req.name,
        grade=req.grade,
        school=req.school,
        subjects=req.subjects,
    )
    db.add(student)
    await db.flush()

    return APIResponse(data=StudentResponse.model_validate(student))


@router.put("/{student_id}", response_model=APIResponse[StudentResponse])
async def update_student(
    student_id: uuid.UUID,
    req: StudentUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """更新孩子档案。"""
    result = await db.execute(select(Student).where(Student.id == student_id))
    student = result.scalar_one_or_none()

    if student is None:
        raise NotFoundException("孩子档案不存在")
    if student.user_id != current_user.id:
        raise ForbiddenException("无权修改该孩子档案")

    if req.name is not None:
        student.name = req.name
    if req.grade is not None:
        valid_grades = ["初一", "初二", "初三"]
        if req.grade not in valid_grades:
            raise BadRequestException(f"年级必须是以下之一：{', '.join(valid_grades)}")
        student.grade = req.grade
    if req.school is not None:
        student.school = req.school
    if req.subjects is not None:
        valid_subjects = ["math", "politics", "history"]
        for subj in req.subjects:
            if subj not in valid_subjects:
                raise BadRequestException(f"不支持的学科：{subj}")
        student.subjects = req.subjects

    await db.flush()
    return APIResponse(data=StudentResponse.model_validate(student))


@router.get("/{student_id}", response_model=APIResponse[StudentResponse])
async def get_student(
    student_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取单个孩子详情。"""
    result = await db.execute(select(Student).where(Student.id == student_id))
    student = result.scalar_one_or_none()

    if student is None:
        raise NotFoundException("孩子档案不存在")
    if student.user_id != current_user.id:
        raise ForbiddenException("无权查看该孩子档案")

    return APIResponse(data=StudentResponse.model_validate(student))


@router.delete("/{student_id}", response_model=APIResponse)
async def delete_student(
    student_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """删除孩子档案。"""
    result = await db.execute(select(Student).where(Student.id == student_id))
    student = result.scalar_one_or_none()

    if student is None:
        raise NotFoundException("孩子档案不存在")
    if student.user_id != current_user.id:
        raise ForbiddenException("无权删除该孩子档案")

    await db.delete(student)
    await db.flush()

    return APIResponse(message="已删除")
