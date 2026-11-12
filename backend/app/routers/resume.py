"""
Resume upload and analysis router.
"""
import uuid
import os
from pathlib import Path
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.user import User
from app.models.student import StudentProfile, CareerGoal
from app.models.resume import Resume
from app.middleware.auth_middleware import get_current_user
from app.agents.resume_agent import run_resume_analysis_agent
from app.llm_gateway.token_budget import check_budget, record_usage
import structlog

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/resume", tags=["Resume"])

UPLOAD_DIR = Path("./uploads/resumes")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def _extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Extract plain text from PDF bytes using PyMuPDF."""
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        text = "\n".join(page.get_text() for page in doc)
        doc.close()
        return text.strip()
    except Exception:
        pass
    # Fallback: try to extract raw text from PDF bytes
    try:
        return pdf_bytes.decode("latin-1", errors="ignore")
    except Exception:
        return ""


def _save_file_locally(file_bytes: bytes, filename: str) -> str:
    """Save uploaded file to local disk."""
    save_path = UPLOAD_DIR / filename
    save_path.write_bytes(file_bytes)
    return str(save_path)


@router.post("/upload")
async def upload_resume(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")
    if file.size and file.size > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size must be under 5MB.")

    profile_result = await db.execute(
        select(StudentProfile).where(StudentProfile.user_id == current_user.id)
    )
    profile = profile_result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Student profile not found.")

    pdf_bytes = await file.read()
    object_name = f"{current_user.id}_{uuid.uuid4()}.pdf"
    file_path = _save_file_locally(pdf_bytes, object_name)
    extracted_text = _extract_text_from_pdf(pdf_bytes)

    # Check existing version count
    existing_result = await db.execute(
        select(Resume).where(Resume.student_id == profile.id)
    )
    existing_resumes = existing_result.scalars().all()
    version = len(existing_resumes) + 1

    resume = Resume(
        student_id=profile.id,
        file_path=file_path,
        original_filename=file.filename,
        version=version,
        extracted_text=extracted_text,
    )
    db.add(resume)
    await db.commit()
    await db.refresh(resume)

    return {
        "resume_id": str(resume.id),
        "version": version,
        "filename": file.filename,
        "text_extracted": bool(extracted_text),
        "message": "Resume uploaded successfully. Run /resume/analyze to get AI analysis.",
    }


@router.post("/analyze/{resume_id}")
async def analyze_resume(
    resume_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    within_budget, _ = await check_budget(str(current_user.id))
    if not within_budget:
        raise HTTPException(status_code=429, detail="Daily AI budget exceeded.")

    resume_result = await db.execute(select(Resume).where(Resume.id == resume_id))
    resume = resume_result.scalar_one_or_none()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found.")

    profile_result = await db.execute(
        select(StudentProfile).where(StudentProfile.id == resume.student_id)
    )
    profile = profile_result.scalar_one_or_none()

    goals_result = await db.execute(
        select(CareerGoal).where(CareerGoal.student_id == profile.id)
    )
    goals = goals_result.scalars().all()

    resume_data = {
        "name": current_user.name,
        "resume_text": resume.extracted_text or "",
        "target_role": goals[0].target_role if goals else "Software Engineer",
        "cgpa": profile.cgpa,
    }

    result = await run_resume_analysis_agent(resume_data)
    analysis = result.get("analysis", {})

    # Update resume record with analysis
    import json as _json
    resume.ats_score = analysis.get("ats_score")
    resume.analysis_json = _json.dumps(analysis)
    await db.commit()

    await record_usage(str(current_user.id), result.get("cost_usd", 0.0))

    return {
        "resume_id": str(resume_id),
        "ats_score": analysis.get("ats_score"),
        "overall_rating": analysis.get("overall_rating"),
        "strengths": analysis.get("strengths", []),
        "critical_issues": analysis.get("critical_issues", []),
        "improvements": analysis.get("improvements", []),
        "missing_keywords": analysis.get("missing_keywords", []),
        "rewritten_summary": analysis.get("rewritten_summary", ""),
        "overall_feedback": analysis.get("overall_feedback", ""),
        "hitl_required": result.get("hitl_required", False),
        "tokens_used": result.get("tokens_used"),
        "cost_usd": result.get("cost_usd"),
    }


@router.get("/history")
async def get_resume_history(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    profile_result = await db.execute(
        select(StudentProfile).where(StudentProfile.user_id == current_user.id)
    )
    profile = profile_result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found.")

    resumes_result = await db.execute(
        select(Resume).where(Resume.student_id == profile.id).order_by(Resume.uploaded_at.desc())
    )
    resumes = resumes_result.scalars().all()
    return [
        {
            "resume_id": str(r.id),
            "version": r.version,
            "filename": r.original_filename,
            "ats_score": r.ats_score,
            "uploaded_at": r.uploaded_at.isoformat(),
        }
        for r in resumes
    ]
