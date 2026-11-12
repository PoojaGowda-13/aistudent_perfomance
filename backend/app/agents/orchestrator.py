"""
Multi-Agent Orchestrator — sequential pipeline coordinator.
Runs Academic → Skill Gap → Career → Learning Path in sequence.
No LangGraph dependency required.
"""
import uuid
import structlog

from app.agents.academic_agent import run_academic_performance_agent
from app.agents.skill_gap_agent import run_skill_gap_agent
from app.agents.career_agent import run_career_recommendation_agent
from app.agents.learning_path_agent import run_learning_path_agent
from app.memory.redis_memory import set_agent_state
from app.observability.langsmith_tracer import trace_agent_call

logger = structlog.get_logger(__name__)


async def run_full_pipeline(student_data: dict, student_id: str) -> dict:
    """
    Run the full 4-agent pipeline sequentially.
    Each agent's output enriches the next agent's input.
    """
    session_id = str(uuid.uuid4())
    logger.info("orchestrator_start", session_id=session_id, student_id=student_id)

    errors = []
    total_tokens = 0
    total_cost = 0.0
    completed = []

    academic_analysis = None
    skill_gap_analysis = None
    career_analysis = None
    learning_path = None

    # ── Step 1: Academic Performance ──────────────────────────────────────────
    try:
        result = await trace_agent_call(run_academic_performance_agent, student_data, agent_name="academic_performance")
        academic_analysis = result.get("analysis")
        total_tokens += result.get("tokens_used", 0)
        total_cost += result.get("cost_usd", 0.0)
        completed.append("academic_performance")
        logger.info("agent_done", agent="academic_performance")
    except Exception as e:
        logger.error("agent_error", agent="academic_performance", error=str(e))
        errors.append(f"academic_performance: {e}")

    # ── Step 2: Skill Gap ──────────────────────────────────────────────────────
    try:
        enriched = {**student_data, "academic_analysis": academic_analysis or {}}
        result = await trace_agent_call(run_skill_gap_agent, enriched, agent_name="skill_gap")
        skill_gap_analysis = result.get("analysis")
        total_tokens += result.get("tokens_used", 0)
        total_cost += result.get("cost_usd", 0.0)
        completed.append("skill_gap")
        logger.info("agent_done", agent="skill_gap")
    except Exception as e:
        logger.error("agent_error", agent="skill_gap", error=str(e))
        errors.append(f"skill_gap: {e}")

    # ── Step 3: Career Recommendation ─────────────────────────────────────────
    try:
        enriched = {
            **student_data,
            "academic_analysis": academic_analysis or {},
            "skill_gap_analysis": skill_gap_analysis or {},
        }
        result = await trace_agent_call(run_career_recommendation_agent, enriched, agent_name="career_recommendation")
        career_analysis = result.get("analysis")
        total_tokens += result.get("tokens_used", 0)
        total_cost += result.get("cost_usd", 0.0)
        completed.append("career_recommendation")
        logger.info("agent_done", agent="career_recommendation")
    except Exception as e:
        logger.error("agent_error", agent="career_recommendation", error=str(e))
        errors.append(f"career_recommendation: {e}")

    # ── Step 4: Learning Path ──────────────────────────────────────────────────
    try:
        top_role = ""
        if career_analysis and "top_recommendations" in career_analysis:
            recs = career_analysis["top_recommendations"]
            if recs:
                top_role = recs[0].get("role", "")

        sg = skill_gap_analysis or {}
        lp_data = {
            **student_data,
            "target_role": top_role or student_data.get("target_role", "Software Engineer"),
            "missing_critical_skills": sg.get("missing_critical_skills", []),
            "missing_high_priority_skills": sg.get("missing_high_priority_skills", []),
        }
        result = await trace_agent_call(run_learning_path_agent, lp_data, agent_name="learning_path")
        learning_path = result.get("analysis")
        total_tokens += result.get("tokens_used", 0)
        total_cost += result.get("cost_usd", 0.0)
        completed.append("learning_path")
        logger.info("agent_done", agent="learning_path")
    except Exception as e:
        logger.error("agent_error", agent="learning_path", error=str(e))
        errors.append(f"learning_path: {e}")

    # ── Persist to memory ──────────────────────────────────────────────────────
    await set_agent_state(session_id, {
        "student_id": student_id,
        "academic_analysis": academic_analysis,
        "skill_gap_analysis": skill_gap_analysis,
        "career_analysis": career_analysis,
        "learning_path": learning_path,
        "completed_agents": completed,
        "total_tokens": total_tokens,
        "total_cost_usd": total_cost,
    })

    logger.info("orchestrator_complete", session_id=session_id, completed=completed, total_cost=total_cost)

    return {
        "session_id": session_id,
        "academic_analysis": academic_analysis,
        "skill_gap_analysis": skill_gap_analysis,
        "career_recommendations": career_analysis,
        "learning_path": learning_path,
        "completed_agents": completed,
        "errors": errors,
        "total_tokens": total_tokens,
        "total_cost_usd": total_cost,
    }
