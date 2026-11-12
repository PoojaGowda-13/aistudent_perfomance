"""
Career Recommendation Agent
Recommends suitable job roles based on academic performance, skills, and interests.
LLM: Anthropic Claude 3.5
"""
import json
from app.llm_gateway.gateway import get_llm_gateway, LLMRequest
from app.memory.chroma_store import query_similar

SYSTEM_PROMPT = """You are a highly experienced career counselor and talent acquisition specialist.
Given a student's complete profile (academics, skills, interests, department), you will:
1. Recommend the top 5 most suitable career paths
2. Explain why each role is a good match
3. Provide a match score (0-100) for each role
4. Mention industry outlook and growth potential
5. Suggest entry-level positions to target

Always return a structured JSON response with actionable career guidance."""

AGENT_TYPE = "career_recommendation"


async def run_career_recommendation_agent(student_data: dict) -> dict:
    """
    student_data = {
        "name": str,
        "cgpa": float,
        "department": str,
        "year_of_study": int,
        "interests": [str],
        "skills": [{"skill_name": str, "proficiency_level": str}],
        "academic_analysis": dict,  # from academic_agent
        "skill_gap_analysis": dict,  # from skill_gap_agent
    }
    """
    gateway = get_llm_gateway()

    interests = student_data.get("interests", [])
    skills = student_data.get("skills", [])
    skills_str = ", ".join([s["skill_name"] for s in skills]) or "None listed"
    interests_str = ", ".join(interests) or "Not specified"

    # Retrieve semantically similar career profiles
    profile_query = f"{student_data.get('department', '')} {interests_str} {skills_str}"
    similar_roles = query_similar("career_profiles", profile_query, n_results=5)
    market_context = "\n".join([r["document"] for r in similar_roles]) if similar_roles else ""

    academic_summary = student_data.get("academic_analysis", {})
    cgpa_band = academic_summary.get("cgpa_band", "Unknown")

    user_message = f"""Recommend suitable career paths for this student:

Student Profile:
- Name: {student_data.get('name', 'Student')}
- Department: {student_data.get('department', 'Computer Science')}
- Year of Study: {student_data.get('year_of_study', 'Final Year')}
- CGPA: {student_data.get('cgpa', 'N/A')} ({cgpa_band})
- Skills: {skills_str}
- Interests: {interests_str}
- Academic Strength: {academic_summary.get('strong_subjects', [])}
- Placement Risk: {academic_summary.get('placement_risk_level', 'Unknown')}

Market Context from Career Database:
{market_context[:1000] if market_context else "General IT/technology market"}

Provide career recommendations in this JSON format:
{{
  "top_recommendations": [
    {{
      "rank": 1,
      "role": "...",
      "industry": "...",
      "match_score": <0-100>,
      "match_reasons": ["..."],
      "key_skills_required": ["..."],
      "skills_already_have": ["..."],
      "skills_to_develop": ["..."],
      "average_salary_inr": "...",
      "growth_outlook": "<Excellent/Good/Fair>",
      "entry_level_titles": ["..."],
      "top_companies": ["..."],
      "career_trajectory": "..."
    }}
  ],
  "not_recommended_roles": [
    {{"role": "...", "reason": "..."}}
  ],
  "overall_career_profile": "...",
  "immediate_next_steps": ["..."],
  "long_term_vision": "..."
}}"""

    request = LLMRequest(
        messages=[{"role": "user", "content": user_message}],
        system_prompt=SYSTEM_PROMPT,
        model="auto",
        max_tokens=2500,
        temperature=0.3,
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
