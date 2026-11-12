import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Float, Integer, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class AcademicRecord(Base):
    __tablename__ = "academic_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    student_id: Mapped[str] = mapped_column(String(36), ForeignKey("student_profiles.id"))
    semester: Mapped[int] = mapped_column(Integer)
    subject_code: Mapped[str] = mapped_column(String(50))
    subject_name: Mapped[str] = mapped_column(String(200))
    marks_obtained: Mapped[float] = mapped_column(Float)
    max_marks: Mapped[float] = mapped_column(Float, default=100.0)
    grade: Mapped[Optional[str]] = mapped_column(String(5))
    grade_points: Mapped[Optional[float]] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    student = relationship("StudentProfile", back_populates="academic_records")
