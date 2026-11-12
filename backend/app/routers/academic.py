import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.models.user import User
from app.models.student import StudentProfile
from app.models.academic import AcademicRecord
from app.schemas.schemas import AcademicRecordCreate, AcademicRecordResponse
from app.middleware.auth_middleware import get_current_user

router = APIRouter(prefix="/academic", tags=["Academic"])


@router.post("/records", response_model=AcademicRecordResponse, status_code=201)
async def add_record(
    payload: AcademicRecordCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(StudentProfile).where(StudentProfile.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Student profile not found")

    record = AcademicRecord(student_id=profile.id, **payload.model_dump())
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record


@router.post("/records/bulk", response_model=List[AcademicRecordResponse], status_code=201)
async def add_records_bulk(
    records: List[AcademicRecordCreate],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(StudentProfile).where(StudentProfile.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Student profile not found")

    new_records = [AcademicRecord(student_id=profile.id, **r.model_dump()) for r in records]
    db.add_all(new_records)
    await db.commit()
    for rec in new_records:
        await db.refresh(rec)
    return new_records


@router.get("/records", response_model=List[AcademicRecordResponse])
async def get_my_records(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(StudentProfile).where(StudentProfile.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Student profile not found")

    records_result = await db.execute(
        select(AcademicRecord)
        .where(AcademicRecord.student_id == profile.id)
        .order_by(AcademicRecord.semester)
    )
    return records_result.scalars().all()


@router.get("/analytics")
async def get_analytics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return CGPA, semester averages, and per-subject performance data for charts."""
    result = await db.execute(
        select(StudentProfile).where(StudentProfile.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Student profile not found")

    records_result = await db.execute(
        select(AcademicRecord).where(AcademicRecord.student_id == profile.id)
    )
    records = records_result.scalars().all()

    if not records:
        return {"cgpa": None, "semester_averages": [], "subject_performance": []}

    # Compute semester averages
    semester_map: dict = {}
    for r in records:
        semester_map.setdefault(r.semester, []).append(r.marks_obtained / r.max_marks * 100)

    semester_averages = [
        {"semester": sem, "average": round(sum(marks) / len(marks), 2)}
        for sem, marks in sorted(semester_map.items())
    ]

    # Compute subject performance
    subject_performance = [
        {
            "subject": r.subject_name,
            "code": r.subject_code,
            "semester": r.semester,
            "percentage": round(r.marks_obtained / r.max_marks * 100, 2),
            "grade": r.grade,
        }
        for r in records
    ]

    # CGPA from grade_points
    grade_points = [r.grade_points for r in records if r.grade_points is not None]
    cgpa = round(sum(grade_points) / len(grade_points), 2) if grade_points else profile.cgpa

    # Identify weak subjects (below 50%)
    weak_subjects = [
        s["subject"] for s in subject_performance if s["percentage"] < 50
    ]

    return {
        "cgpa": cgpa,
        "total_subjects": len(records),
        "semester_averages": semester_averages,
        "subject_performance": subject_performance,
        "weak_subjects": weak_subjects,
    }
