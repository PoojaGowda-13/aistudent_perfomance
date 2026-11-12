import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.user import User
from app.models.student import StudentProfile, StudentSkill, CareerGoal
from app.schemas.schemas import (
    StudentProfileCreate, StudentProfileResponse,
    SkillCreate, SkillResponse,
    CareerGoalCreate, CareerGoalResponse,
    UserResponse,
)
from app.middleware.auth_middleware import get_current_user

router = APIRouter(prefix="/students", tags=["Students"])


@router.get("/me/profile", response_model=StudentProfileResponse)
async def get_my_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(StudentProfile).where(StudentProfile.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile


@router.put("/me/profile", response_model=StudentProfileResponse)
async def update_my_profile(
    payload: StudentProfileCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(StudentProfile).where(StudentProfile.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        profile = StudentProfile(user_id=current_user.id)
        db.add(profile)

    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(profile, field, value)

    await db.commit()
    await db.refresh(profile)
    return profile


@router.get("/me/skills", response_model=list[SkillResponse])
async def get_my_skills(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(StudentProfile).where(StudentProfile.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    skills_result = await db.execute(
        select(StudentSkill).where(StudentSkill.student_id == profile.id)
    )
    return skills_result.scalars().all()


@router.post("/me/skills", response_model=SkillResponse, status_code=201)
async def add_skill(
    payload: SkillCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(StudentProfile).where(StudentProfile.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    skill = StudentSkill(student_id=profile.id, **payload.model_dump())
    db.add(skill)
    await db.commit()
    await db.refresh(skill)
    return skill


@router.post("/me/career-goals", response_model=CareerGoalResponse, status_code=201)
async def add_career_goal(
    payload: CareerGoalCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(StudentProfile).where(StudentProfile.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    goal = CareerGoal(student_id=profile.id, **payload.model_dump())
    db.add(goal)
    await db.commit()
    await db.refresh(goal)
    return goal


@router.get("/me/career-goals", response_model=list[CareerGoalResponse])
async def get_career_goals(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(StudentProfile).where(StudentProfile.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    goals_result = await db.execute(
        select(CareerGoal).where(CareerGoal.student_id == profile.id)
    )
    return goals_result.scalars().all()
