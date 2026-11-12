"""
Agents router — exposes all AI agent endpoints with auth, guardrails, and audit logging.
"""
import uuid
import hashlib
import time
import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.user import User
from app.models.student import StudentProfile, StudentSkill, CareerGoal, InterviewSession, LearningPath
from app.models.academic import AcademicRecord
from app.models.agent_session import AgentSession, TokenUsage
from app.schemas.schemas import AgentRunResponse, InterviewStartRequest, InterviewEvaluateRequest
from app.middleware.auth_middleware import get_current_user
from app.llm_gateway.token_budget import check_budget, record_usage
from app.guardrails.validators import sanitize_input
from app.agents.orchestrator import run_full_pipeline
from app.agents.academic_agent import run_academic_performance_agent
from app.agents.skill_gap_agent import run_skill_gap_agent
from app.agents.career_agent import run_career_recommendation_agent
from app.agents.learning_path_agent import run_learning_path_agent
from app.agents.interview_agent import generate_interview_questions, evaluate_interview_answer
import structlog

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/agents", tags=["AI Agents"])


async def _get_student_context(user: User, db: AsyncSession) -> dict:
    """Build a rich student context dict for agent consumption."""
    profile_result = await db.execute(
        select(StudentProfile).where(StudentProfile.user_id == user.id)
    )
    profile = profile_result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Student profile not found. Please complete your profile first.")

    records_result = await db.execute(
        select(AcademicRecord).where(AcademicRecord.student_id == profile.id)
    )
    records = records_result.scalars().all()

    skills_result = await db.execute(
        select(StudentSkill).where(StudentSkill.student_id == profile.id)
    )
    skills = skills_result.scalars().all()

    goals_result = await db.execute(
        select(CareerGoal).where(CareerGoal.student_id == profile.id)
    )
    goals = goals_result.scalars().all()

    # Compute semester averages inline
    semester_map: dict = {}
    for r in records:
        semester_map.setdefault(r.semester, []).append(r.marks_obtained / r.max_marks * 100)
    semester_averages = [
        {"semester": s, "average": round(sum(m) / len(m), 2)}
        for s, m in sorted(semester_map.items())
    ]

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

    weak_subjects = [sp["subject"] for sp in subject_performance if sp["percentage"] < 50]

    grade_points = [r.grade_points for r in records if r.grade_points]
    cgpa = round(sum(grade_points) / len(grade_points), 2) if grade_points else profile.cgpa

    return {
        "name": user.name,
        "cgpa": cgpa,
        "department": profile.department,
        "year_of_study": profile.year_of_study,
        "interests": profile.interests or [],
        "linkedin_url": profile.linkedin_url,
        "current_skills": [{"skill_name": s.skill_name, "proficiency_level": s.proficiency_level} for s in skills],
        "target_role": goals[0].target_role if goals else "Software Engineer",
        "target_industry": goals[0].target_industry if goals else "Technology",
        "timeline_months": goals[0].timeline_months if goals else 6,
        "semester_averages": semester_averages,
        "subject_performance": subject_performance,
        "weak_subjects": weak_subjects,
        "profile_id": str(profile.id),
    }


async def _log_agent_session(
    db: AsyncSession,
    user_id: str,
    agent_type: str,
    session_id: str,
    input_summary: str,
    output: dict,
    tokens: int,
    cost: float,
    model: str,
    latency_ms: int,
    hitl_required: bool = False,
):
    provider = model.split("/")[0] if model else "unknown"
    model_name = model.split("/")[-1] if model else "unknown"
    input_hash = hashlib.sha256(input_summary.encode()).hexdigest()[:16]

    session = AgentSession(
        user_id=user_id,
        agent_type=agent_type,
        session_id=session_id,
        input_hash=input_hash,
        input_summary=input_summary[:500],
        output_json=json.dumps(output) if output else None,
        tokens_used=tokens,
        cost_usd=cost,
        llm_provider=provider,
        model_name=model_name,
        latency_ms=latency_ms,
        hitl_required=hitl_required,
    )
    db.add(session)

    usage = TokenUsage(
        agent_type=agent_type,
        llm_provider=provider,
        model_name=model_name,
        input_tokens=tokens // 2,
        output_tokens=tokens // 2,
        cost_usd=cost,
    )
    db.add(usage)
    await db.commit()


@router.post("/full-pipeline", response_model=AgentRunResponse)
async def run_full_agent_pipeline(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Run all 4 core agents in sequence: Academic → Skill Gap → Career → Learning Path."""
    # Budget check
    within_budget, spend = await check_budget(str(current_user.id))
    if not within_budget:
        raise HTTPException(status_code=429, detail=f"Daily AI budget exceeded (${spend:.4f}). Try again tomorrow.")

    start = time.time()
    student_data = await _get_student_context(current_user, db)

    result = await run_full_pipeline(student_data, str(current_user.id))

    latency_ms = int((time.time() - start) * 1000)
    await record_usage(str(current_user.id), result.get("total_cost_usd", 0.0))

    await _log_agent_session(
        db, current_user.id, "full_pipeline", result["session_id"],
        f"Full pipeline for {student_data['name']}",
        result, result.get("total_tokens", 0), result.get("total_cost_usd", 0.0),
        "multi-agent", latency_ms,
    )

    return AgentRunResponse(
        session_id=result["session_id"],
        agent_type="full_pipeline",
        result=result,
        tokens_used=result.get("total_tokens"),
        cost_usd=result.get("total_cost_usd"),
        message="Full analysis pipeline completed successfully",
    )


@router.post("/analyze-performance", response_model=AgentRunResponse)
async def analyze_performance(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    within_budget, _ = await check_budget(str(current_user.id))
    if not within_budget:
        raise HTTPException(status_code=429, detail="Daily AI budget exceeded.")

    start = time.time()
    student_data = await _get_student_context(current_user, db)
    result = await run_academic_performance_agent(student_data)
    latency_ms = int((time.time() - start) * 1000)

    await record_usage(str(current_user.id), result.get("cost_usd", 0.0))
    session_id = str(uuid.uuid4())
    await _log_agent_session(
        db, current_user.id, "academic_performance", session_id,
        f"Academic analysis for {student_data['name']}",
        result, result.get("tokens_used", 0), result.get("cost_usd", 0.0),
        result.get("model", ""), latency_ms,
    )

    return AgentRunResponse(
        session_id=session_id,
        agent_type="academic_performance",
        result=result["analysis"],
        tokens_used=result.get("tokens_used"),
        cost_usd=result.get("cost_usd"),
    )


@router.post("/detect-skill-gaps", response_model=AgentRunResponse)
async def detect_skill_gaps(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    within_budget, _ = await check_budget(str(current_user.id))
    if not within_budget:
        raise HTTPException(status_code=429, detail="Daily AI budget exceeded.")

    start = time.time()
    student_data = await _get_student_context(current_user, db)
    result = await run_skill_gap_agent(student_data)
    latency_ms = int((time.time() - start) * 1000)

    await record_usage(str(current_user.id), result.get("cost_usd", 0.0))
    session_id = str(uuid.uuid4())
    await _log_agent_session(
        db, current_user.id, "skill_gap", session_id,
        f"Skill gap analysis for {student_data['name']}",
        result, result.get("tokens_used", 0), result.get("cost_usd", 0.0),
        result.get("model", ""), latency_ms,
    )

    return AgentRunResponse(
        session_id=session_id,
        agent_type="skill_gap",
        result=result["analysis"],
        tokens_used=result.get("tokens_used"),
        cost_usd=result.get("cost_usd"),
    )


@router.post("/career-recommendations", response_model=AgentRunResponse)
async def get_career_recommendations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    within_budget, _ = await check_budget(str(current_user.id))
    if not within_budget:
        raise HTTPException(status_code=429, detail="Daily AI budget exceeded.")

    start = time.time()
    student_data = await _get_student_context(current_user, db)
    result = await run_career_recommendation_agent(student_data)
    latency_ms = int((time.time() - start) * 1000)

    await record_usage(str(current_user.id), result.get("cost_usd", 0.0))
    session_id = str(uuid.uuid4())
    await _log_agent_session(
        db, current_user.id, "career_recommendation", session_id,
        f"Career recommendations for {student_data['name']}",
        result, result.get("tokens_used", 0), result.get("cost_usd", 0.0),
        result.get("model", ""), latency_ms,
    )

    return AgentRunResponse(
        session_id=session_id,
        agent_type="career_recommendation",
        result=result["analysis"],
        tokens_used=result.get("tokens_used"),
        cost_usd=result.get("cost_usd"),
    )


@router.post("/learning-path", response_model=AgentRunResponse)
async def generate_learning_path(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    within_budget, _ = await check_budget(str(current_user.id))
    if not within_budget:
        raise HTTPException(status_code=429, detail="Daily AI budget exceeded.")

    start = time.time()
    student_data = await _get_student_context(current_user, db)

    # Run skill gap first to get missing skills
    skill_result = await run_skill_gap_agent(student_data)
    skill_analysis = skill_result.get("analysis", {})

    lp_data = {
        **student_data,
        "missing_critical_skills": skill_analysis.get("missing_critical_skills", []),
        "missing_high_priority_skills": skill_analysis.get("missing_high_priority_skills", []),
    }

    result = await run_learning_path_agent(lp_data)
    latency_ms = int((time.time() - start) * 1000)
    total_cost = skill_result.get("cost_usd", 0.0) + result.get("cost_usd", 0.0)

    await record_usage(str(current_user.id), total_cost)
    session_id = str(uuid.uuid4())

    # Persist learning path to DB
    profile_result = await db.execute(
        select(StudentProfile).where(StudentProfile.user_id == current_user.id)
    )
    profile = profile_result.scalar_one_or_none()
    if profile:
        lp = LearningPath(
            student_id=profile.id,
            role_target=student_data.get("target_role", ""),
            roadmap_json=result.get("analysis", {}),
        )
        db.add(lp)
        await db.commit()

    await _log_agent_session(
        db, current_user.id, "learning_path", session_id,
        f"Learning path for {student_data['name']}",
        result, result.get("tokens_used", 0), total_cost,
        result.get("model", ""), latency_ms,
    )

    return AgentRunResponse(
        session_id=session_id,
        agent_type="learning_path",
        result=result["analysis"],
        tokens_used=result.get("tokens_used"),
        cost_usd=total_cost,
    )


@router.post("/interview/start", response_model=AgentRunResponse)
async def start_interview(
    payload: InterviewStartRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    within_budget, _ = await check_budget(str(current_user.id))
    if not within_budget:
        raise HTTPException(status_code=429, detail="Daily AI budget exceeded.")

    start = time.time()
    student_data = await _get_student_context(current_user, db)
    skills = [s["skill_name"] for s in student_data.get("current_skills", [])]

    q_data = {
        "name": student_data["name"],
        "role": payload.role,
        "skills": skills,
        "experience_level": "Fresher",
        "num_questions": payload.num_questions,
    }

    result = await generate_interview_questions(q_data)
    latency_ms = int((time.time() - start) * 1000)

    # Save interview session
    profile_result = await db.execute(
        select(StudentProfile).where(StudentProfile.user_id == current_user.id)
    )
    profile = profile_result.scalar_one_or_none()
    interview_session_id = str(uuid.uuid4())

    if profile:
        interview_db = InterviewSession(
            id=interview_session_id,
            student_id=profile.id,
            role=payload.role,
            questions_json=json.dumps(result.get("analysis", {})),
        )
        db.add(interview_db)
        await db.commit()

    await record_usage(str(current_user.id), result.get("cost_usd", 0.0))

    return AgentRunResponse(
        session_id=interview_session_id,
        agent_type="interview_prep",
        result=result.get("analysis", {}),
        tokens_used=result.get("tokens_used"),
        cost_usd=result.get("cost_usd"),
        message=f"Generated {payload.num_questions} interview questions for {payload.role}",
    )


@router.post("/interview/evaluate", response_model=AgentRunResponse)
async def evaluate_answer(
    payload: InterviewEvaluateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    within_budget, _ = await check_budget(str(current_user.id))
    if not within_budget:
        raise HTTPException(status_code=429, detail="Daily AI budget exceeded.")

    # Sanitize answer for prompt injection
    clean_answer, was_flagged = sanitize_input(payload.answer)
    if was_flagged:
        raise HTTPException(status_code=400, detail="Input contains disallowed content.")

    # Fetch the interview session
    session_result = await db.execute(
        select(InterviewSession).where(InterviewSession.id == payload.session_id)
    )
    interview_session = session_result.scalar_one_or_none()
    if not interview_session:
        raise HTTPException(status_code=404, detail="Interview session not found.")

    questions_data = json.loads(interview_session.questions_json or "{}") if isinstance(interview_session.questions_json, str) else (interview_session.questions_json or {})
    questions = questions_data.get("questions", [])
    if payload.question_index >= len(questions):
        raise HTTPException(status_code=400, detail="Invalid question index.")

    question = questions[payload.question_index]

    start = time.time()
    eval_data = {
        "role": interview_session.role,
        "question": question.get("question", ""),
        "question_type": question.get("type", "Technical"),
        "student_answer": clean_answer,
        "key_criteria": question.get("key_evaluation_criteria", []),
    }

    result = await evaluate_interview_answer(eval_data)
    latency_ms = int((time.time() - start) * 1000)

    await record_usage(str(current_user.id), result.get("cost_usd", 0.0))

    return AgentRunResponse(
        session_id=str(payload.session_id),
        agent_type="interview_prep",
        result=result.get("evaluation", {}),
        tokens_used=result.get("tokens_used"),
        cost_usd=result.get("cost_usd"),
        hitl_required=result.get("hitl_required", False),
        message="Answer evaluated" + (" — flagged for human review" if result.get("hitl_required") else ""),
    )
