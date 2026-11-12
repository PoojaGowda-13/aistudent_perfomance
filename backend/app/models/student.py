import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Float, Integer, ForeignKey, DateTime, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class StudentProfile(Base):
    __tablename__ = "student_profiles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), unique=True)
    department: Mapped[Optional[str]] = mapped_column(String(150))
    year_of_study: Mapped[Optional[int]] = mapped_column(Integer)
    cgpa: Mapped[Optional[float]] = mapped_column(Float)
    interests: Mapped[Optional[str]] = mapped_column(Text, default="")  # stored as comma-separated
    linkedin_url: Mapped[Optional[str]] = mapped_column(String(500))
    github_url: Mapped[Optional[str]] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="profile")
    academic_records = relationship("AcademicRecord", back_populates="student", cascade="all, delete-orphan")
    skills = relationship("StudentSkill", back_populates="student", cascade="all, delete-orphan")
    career_goals = relationship("CareerGoal", back_populates="student", cascade="all, delete-orphan")
    learning_paths = relationship("LearningPath", back_populates="student", cascade="all, delete-orphan")
    resumes = relationship("Resume", back_populates="student", cascade="all, delete-orphan")
    interview_sessions = relationship("InterviewSession", back_populates="student", cascade="all, delete-orphan")


class StudentSkill(Base):
    __tablename__ = "student_skills"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    student_id: Mapped[str] = mapped_column(String(36), ForeignKey("student_profiles.id"))
    skill_name: Mapped[str] = mapped_column(String(200))
    proficiency_level: Mapped[str] = mapped_column(String(50), default="beginner")
    verified: Mapped[bool] = mapped_column(default=False)
    source: Mapped[str] = mapped_column(String(100), default="self_declared")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    student = relationship("StudentProfile", back_populates="skills")


class CareerGoal(Base):
    __tablename__ = "career_goals"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    student_id: Mapped[str] = mapped_column(String(36), ForeignKey("student_profiles.id"))
    target_role: Mapped[str] = mapped_column(String(200))
    target_industry: Mapped[Optional[str]] = mapped_column(String(200))
    timeline_months: Mapped[Optional[int]] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    student = relationship("StudentProfile", back_populates="career_goals")


class LearningPath(Base):
    __tablename__ = "learning_paths"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    student_id: Mapped[str] = mapped_column(String(36), ForeignKey("student_profiles.id"))
    role_target: Mapped[str] = mapped_column(String(200))
    roadmap_json: Mapped[Optional[str]] = mapped_column(Text)  # JSON as text for SQLite
    progress_pct: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    student = relationship("StudentProfile", back_populates="learning_paths")


class InterviewSession(Base):
    __tablename__ = "interview_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    student_id: Mapped[str] = mapped_column(String(36), ForeignKey("student_profiles.id"))
    role: Mapped[str] = mapped_column(String(200))
    questions_json: Mapped[Optional[str]] = mapped_column(Text)
    answers_json: Mapped[Optional[str]] = mapped_column(Text)
    scores_json: Mapped[Optional[str]] = mapped_column(Text)
    overall_score: Mapped[Optional[float]] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    student = relationship("StudentProfile", back_populates="interview_sessions")
