"""
Academic Performance Analysis Agent
Analyzes student marks, CGPA, subject performance, and identifies academic weaknesses.
LLM: IBM watsonx granite-13b
"""
import json
from app.llm_gateway.gateway import get_llm_gateway, LLMRequest

SYSTEM_PROMPT = """You are an expert academic performance analyst for university students.
Given a student's academic records, you will:
1. Identify weak subjects (below 50% marks) and borderline subjects (50-60%)
2. Assess CGPA trends across semesters
3. Provide actionable improvement suggestions for each weak area
4. Flag high-risk areas that may affect placement eligibility
5. Give an overall academic health score (0-10)

Always return a structured JSON response."""

AGENT_TYPE = "academic_performance"


async def run_academic_performance_agent(student_data: dict) -> dict:
    """
    student_data = {
        "name": str,
        "cgpa": float,
        "semester_averages": [...],
        "subject_performance": [...],
        "weak_subjects": [...],
    }
    """
    gateway = get_llm_gateway()

    user_message = f"""Analyze the following student's academic performance:

Student Name: {student_data.get('name', 'Student')}
Current CGPA: {student_data.get('cgpa', 'N/A')}

Semester Performance:
{json.dumps(student_data.get('semester_averages', []), indent=2)}

Subject-wise Performance:
{json.dumps(student_data.get('subject_performance', []), indent=2)}

Weak Subjects identified: {', '.join(student_data.get('weak_subjects', [])) or 'None'}

Please provide a comprehensive academic analysis in the following JSON format:
{{
  "academic_health_score": <0-10>,
  "cgpa_assessment": "<Good/Average/Poor/Critical>",
  "cgpa_band": "<8-10/6-8/4-6/below-4>",
  "semester_trend": "<Improving/Stable/Declining>",
  "weak_subjects": [
    {{"subject": "...", "percentage": ..., "severity": "critical/moderate/mild", "improvement_tip": "..."}}
  ],
  "strong_subjects": ["..."],
  "placement_risk_level": "<Low/Medium/High/Critical>",
  "placement_cgpa_eligible": <true/false>,
  "key_recommendations": ["...", "...", "..."],
  "priority_focus_areas": ["..."],
  "overall_summary": "..."
}}"""

    request = LLMRequest(
        messages=[{"role": "user", "content": user_message}],
        system_prompt=SYSTEM_PROMPT,
        model="auto",
        max_tokens=1500,
        temperature=0.2,
    )

    llm_response = await gateway.complete(request, agent_type=AGENT_TYPE)

    # Parse JSON from LLM output
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
