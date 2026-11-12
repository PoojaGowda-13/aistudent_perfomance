"""
Skill Gap Detection Agent
Identifies missing technical and professional skills based on career goals.
LLM: OpenAI GPT-4o
"""
import json
from app.llm_gateway.gateway import get_llm_gateway, LLMRequest
from app.memory.chroma_store import query_similar

SYSTEM_PROMPT = """You are an expert technical skills analyst with deep knowledge of the job market.
Given a student's current skills and their target career role, you will:
1. Identify all critical skills required for the target role
2. Compare against the student's existing skills
3. Rank missing skills by market demand and importance
4. Estimate learning time for each missing skill
5. Suggest the best way to acquire each skill

Always return a structured JSON response."""

AGENT_TYPE = "skill_gap"


async def run_skill_gap_agent(student_data: dict) -> dict:
    """
    student_data = {
        "name": str,
        "current_skills": [{"skill_name": str, "proficiency_level": str}],
        "target_role": str,
        "target_industry": str,
        "cgpa": float,
        "department": str,
    }
    """
    gateway = get_llm_gateway()

    # Retrieve similar career profiles from vector DB
    role = student_data.get("target_role", "Software Engineer")
    similar_profiles = query_similar("career_profiles", role, n_results=3)
    context_profiles = "\n".join([p["document"] for p in similar_profiles]) if similar_profiles else ""

    current_skills = student_data.get("current_skills", [])
    skills_list = ", ".join([f"{s['skill_name']} ({s['proficiency_level']})" for s in current_skills]) or "No skills listed"

    user_message = f"""Perform a comprehensive skill gap analysis:

Student: {student_data.get('name', 'Student')}
Department: {student_data.get('department', 'Computer Science')}
CGPA: {student_data.get('cgpa', 'N/A')}
Target Role: {role}
Target Industry: {student_data.get('target_industry', 'Technology')}

Current Skills: {skills_list}

Industry Context (from career profiles database):
{context_profiles[:1000] if context_profiles else "No additional context available"}

Provide a detailed skill gap analysis in the following JSON format:
{{
  "target_role": "{role}",
  "required_skills": [
    {{
      "skill": "...",
      "category": "technical/soft/domain",
      "importance": "critical/high/medium/low",
      "current_proficiency": "none/beginner/intermediate/advanced",
      "gap_severity": "major/moderate/minor",
      "estimated_learning_weeks": <number>,
      "learning_approach": "..."
    }}
  ],
  "missing_critical_skills": ["..."],
  "missing_high_priority_skills": ["..."],
  "skills_to_improve": [
    {{"skill": "...", "current": "...", "target": "...", "suggestion": "..."}}
  ],
  "existing_strengths": ["..."],
  "overall_readiness_score": <0-100>,
  "readiness_level": "<Not Ready/Beginner/Developing/Ready/Highly Ready>",
  "estimated_total_preparation_weeks": <number>,
  "priority_action_items": ["..."]
}}"""

    request = LLMRequest(
        messages=[{"role": "user", "content": user_message}],
        system_prompt=SYSTEM_PROMPT,
        model="auto",
        max_tokens=2000,
        temperature=0.2,
    )

    llm_response = await gateway.complete(request, agent_type=AGENT_TYPE)

    content = llm_response.content.strip()
    if "```json" in content:
        content = content.split("```json")[1].split("```")[0].strip()
    elif "```" in content:
        content = content.split("```")[1].split("```")[0].strip()

    try:
        result = json.loads(content)
    except json.JSONDecodeError:
        result = {"raw_analysis": llm_response.content, "parse_error": True}

    return {
        "agent_type": AGENT_TYPE,
        "analysis": result,
        "tokens_used": llm_response.input_tokens + llm_response.output_tokens,
        "cost_usd": llm_response.cost_usd,
        "model": llm_response.model,
        "latency_ms": llm_response.latency_ms,
    }
