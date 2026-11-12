from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, field_validator


# ─── Auth Schemas ────────────────────────────────────────────────────────────

class UserRegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: str = "student"

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    name: str
    role: str


# ─── User Schemas ─────────────────────────────────────────────────────────────

class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    role: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Student Profile Schemas ──────────────────────────────────────────────────

class StudentProfileCreate(BaseModel):
    department: Optional[str] = None
    year_of_study: Optional[int] = None
    cgpa: Optional[float] = None
    interests: Optional[str] = ""
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None


class StudentProfileResponse(BaseModel):
    id: str
    user_id: str
    department: Optional[str]
    year_of_study: Optional[int]
    cgpa: Optional[float]
    interests: Optional[str]
    linkedin_url: Optional[str]
    github_url: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Skill Schemas ────────────────────────────────────────────────────────────

class SkillCreate(BaseModel):
    skill_name: str
    proficiency_level: str = "beginner"
    source: str = "self_declared"


class SkillResponse(BaseModel):
    id: str
    skill_name: str
    proficiency_level: str
    verified: bool
    source: str

    class Config:
        from_attributes = True


# ─── Career Goal Schemas ──────────────────────────────────────────────────────

class CareerGoalCreate(BaseModel):
    target_role: str
    target_industry: Optional[str] = None
    timeline_months: Optional[int] = None


class CareerGoalResponse(BaseModel):
    id: str
    target_role: str
    target_industry: Optional[str]
    timeline_months: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Academic Record Schemas ──────────────────────────────────────────────────

class AcademicRecordCreate(BaseModel):
    semester: int
    subject_code: str
    subject_name: str
    marks_obtained: float
    max_marks: float = 100.0
    grade: Optional[str] = None
    grade_points: Optional[float] = None


class AcademicRecordResponse(BaseModel):
    id: str
    semester: int
    subject_code: str
    subject_name: str
    marks_obtained: float
    max_marks: float
    grade: Optional[str]
    grade_points: Optional[float]

    class Config:
        from_attributes = True


# ─── Agent Request/Response Schemas ──────────────────────────────────────────

class AgentRunRequest(BaseModel):
    student_id: Optional[str] = None
    additional_context: Optional[dict] = None


class AgentRunResponse(BaseModel):
    session_id: str
    agent_type: str
    result: dict
    tokens_used: Optional[int]
    cost_usd: Optional[float]
    hitl_required: bool = False
    message: str = "Success"


# ─── Interview Schemas ────────────────────────────────────────────────────────

class InterviewStartRequest(BaseModel):
    role: str
    num_questions: int = 5


class InterviewEvaluateRequest(BaseModel):
    session_id: str
    question_index: int
    answer: str


# ─── Resume Analysis Schema ───────────────────────────────────────────────────

class ResumeAnalysisResponse(BaseModel):
    resume_id: str
    ats_score: float
    strengths: List[str]
    improvements: List[str]
    missing_keywords: List[str]
    overall_feedback: str
