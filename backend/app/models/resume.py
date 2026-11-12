import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Float, Integer, ForeignKey, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Resume(Base):
    __tablename__ = "resumes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    student_id: Mapped[str] = mapped_column(String(36), ForeignKey("student_profiles.id"))
    file_path: Mapped[str] = mapped_column(String(500))
    original_filename: Mapped[str] = mapped_column(String(255))
    version: Mapped[int] = mapped_column(Integer, default=1)
    ats_score: Mapped[Optional[float]] = mapped_column(Float)
    analysis_json: Mapped[Optional[str]] = mapped_column(Text)  # JSON as text
    extracted_text: Mapped[Optional[str]] = mapped_column(Text)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    student = relationship("StudentProfile", back_populates="resumes")
