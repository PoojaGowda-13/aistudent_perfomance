"""
Admin dashboard router — user management, agent usage analytics, and cost monitoring.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
from app.database import get_db
from app.models.user import User
from app.models.agent_session import AgentSession, TokenUsage
from app.models.resume import Resume
from app.models.student import StudentProfile
from app.middleware.auth_middleware import require_admin
from datetime import datetime, timedelta

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/dashboard")
async def admin_dashboard(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Admin overview: total users, total agent calls, total cost, HITL queue."""
    total_users = await db.scalar(select(func.count(User.id)))
    total_students = await db.scalar(
        select(func.count(StudentProfile.id))
    )
    total_agent_calls = await db.scalar(select(func.count(AgentSession.id)))
    total_cost = await db.scalar(select(func.sum(AgentSession.cost_usd))) or 0.0

    hitl_pending = await db.scalar(
        select(func.count(AgentSession.id)).where(
            AgentSession.hitl_required == True,
            AgentSession.hitl_approved == None,
        )
    )

    total_resumes = await db.scalar(select(func.count(Resume.id)))

    # Agent type breakdown
    agent_stats_result = await db.execute(
        select(AgentSession.agent_type, func.count(AgentSession.id).label("count"))
        .group_by(AgentSession.agent_type)
    )
    agent_breakdown = [{"agent": row.agent_type, "count": row.count} for row in agent_stats_result]

    return {
        "overview": {
            "total_users": total_users,
            "total_students": total_students,
            "total_agent_calls": total_agent_calls,
            "total_cost_usd": round(total_cost, 4),
            "hitl_pending_reviews": hitl_pending,
            "total_resumes_uploaded": total_resumes,
        },
        "agent_breakdown": agent_breakdown,
    }


@router.get("/token-usage")
async def get_token_usage(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """LLM token usage and cost breakdown by provider and model."""
    usage_result = await db.execute(
        select(
            TokenUsage.llm_provider,
            TokenUsage.model_name,
            func.sum(TokenUsage.input_tokens).label("total_input"),
            func.sum(TokenUsage.output_tokens).label("total_output"),
            func.sum(TokenUsage.cost_usd).label("total_cost"),
            func.count(TokenUsage.id).label("calls"),
        ).group_by(TokenUsage.llm_provider, TokenUsage.model_name)
    )
    return {
        "usage_by_provider": [
            {
                "provider": row.llm_provider,
                "model": row.model_name,
                "total_input_tokens": row.total_input,
                "total_output_tokens": row.total_output,
                "total_cost_usd": round(row.total_cost, 6),
                "calls": row.calls,
            }
            for row in usage_result
        ]
    }


@router.get("/hitl-queue")
async def get_hitl_queue(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """List all agent outputs pending human review."""
    result = await db.execute(
        select(AgentSession)
        .where(AgentSession.hitl_required == True, AgentSession.hitl_approved == None)
        .order_by(AgentSession.created_at.desc())
        .limit(50)
    )
    sessions = result.scalars().all()
    return [
        {
            "id": str(s.id),
            "agent_type": s.agent_type,
            "user_id": str(s.user_id),
            "input_summary": s.input_summary,
            "created_at": s.created_at.isoformat(),
        }
        for s in sessions
    ]


@router.post("/hitl-queue/{session_id}/approve")
async def approve_hitl(
    session_id: str,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(AgentSession).where(AgentSession.id == session_id)
    )
    session = result.scalar_one_or_none()
    if not session:
        return {"error": "Session not found"}
    session.hitl_approved = True
    await db.commit()
    return {"status": "approved", "session_id": session_id}


@router.get("/users")
async def list_users(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(User).order_by(User.created_at.desc()).limit(100)
    )
    users = result.scalars().all()
    return [
        {
            "id": str(u.id),
            "name": u.name,
            "email": u.email,
            "role": u.role.value,
            "is_active": u.is_active,
            "created_at": u.created_at.isoformat(),
        }
        for u in users
    ]
