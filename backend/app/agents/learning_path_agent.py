"""
Learning Path Generator Agent
Generates personalized week-by-week learning roadmaps and course recommendations.
LLM: OpenAI GPT-4o
"""
import json
from app.llm_gateway.gateway import get_llm_gateway, LLMRequest
from app.memory.chroma_store import query_similar

SYSTEM_PROMPT = """You are an expert learning path designer and educational consultant.
Given a student's target role, skill gaps, and timeline, you will:
1. Create a structured week-by-week learning roadmap
2. Recommend specific, real courses (Coursera, Udemy, NPTEL, YouTube, freeCodeCamp)
3. Set measurable milestones and checkpoints
4. Balance theory with hands-on projects
5. Include free and paid resources

Always return a structured JSON roadmap."""

AGENT_TYPE = "learning_path"


async def run_learning_path_agent(student_data: dict) -> dict:
    """
    student_data = {
        "name": str,
        "target_role": str,
        "missing_critical_skills": [str],
        "missing_high_priority_skills": [str],
        "timeline_months": int,
        "current_skills": [str],
        "cgpa": float,
    }
    """
    gateway = get_llm_gateway()

    target_role = student_data.get("target_role", "Software Engineer")
    timeline_months = student_data.get("timeline_months", 6)
    critical_skills = student_data.get("missing_critical_skills", [])
    high_skills = student_data.get("missing_high_priority_skills", [])

    # Get course recommendations from vector DB
    course_query = f"{target_role} {' '.join(critical_skills[:3])}"
    similar_courses = query_similar("course_catalog", course_query, n_results=5)
    course_context = "\n".join([c["document"] for c in similar_courses]) if similar_courses else ""

    skills_to_learn = critical_skills + high_skills
    skills_str = ", ".join(skills_to_learn[:10]) if skills_to_learn else "Programming, DSA, System Design"

    user_message = f"""Create a personalized learning roadmap:

Student: {student_data.get('name', 'Student')}
Target Role: {target_role}
Timeline: {timeline_months} months
Skills to Learn: {skills_str}
Already Knows: {', '.join(student_data.get('current_skills', [])) or 'Basic programming'}

Available Courses Context:
{course_context[:800] if course_context else "Standard online learning platforms"}

Generate a complete learning roadmap in this JSON format:
{{
  "target_role": "{target_role}",
  "total_duration_weeks": <number>,
  "phases": [
    {{
      "phase_number": 1,
      "phase_name": "Foundation",
      "weeks": "1-4",
      "objectives": ["..."],
      "topics": ["..."],
      "courses": [
        {{
          "title": "...",
          "platform": "Coursera/Udemy/NPTEL/YouTube/freeCodeCamp",
          "url_hint": "...",
          "duration_hours": <number>,
          "cost": "Free/Paid",
          "priority": "Must/Recommended/Optional"
        }}
      ],
      "projects": [
        {{"title": "...", "description": "...", "skills_practiced": ["..."]}}
      ],
      "milestone": "...",
      "assessment": "..."
    }}
  ],
  "weekly_time_commitment_hours": <number>,
  "recommended_resources": [
    {{"type": "Book/Blog/YouTube", "name": "...", "topic": "..."}}
  ],
  "mock_interview_schedule": "...",
  "success_metrics": ["..."],
  "final_project_idea": "..."
}}"""

    request = LLMRequest(
        messages=[{"role": "user", "content": user_message}],
        system_prompt=SYSTEM_PROMPT,
        model="auto",
        max_tokens=3000,
        temperature=0.4,
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
        result = {"raw_roadmap": llm_response.content, "parse_error": True}

    return {
        "agent_type": AGENT_TYPE,
        "analysis": result,
        "tokens_used": llm_response.input_tokens + llm_response.output_tokens,
        "cost_usd": llm_response.cost_usd,
        "model": llm_response.model,
        "latency_ms": llm_response.latency_ms,
    }
