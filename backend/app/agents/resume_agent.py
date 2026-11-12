"""
Resume Analysis Agent
Analyzes uploaded resumes and suggests improvements for ATS and readability.
LLM: Anthropic Claude 3.5
"""
import json
from app.llm_gateway.gateway import get_llm_gateway, LLMRequest

SYSTEM_PROMPT = """You are an expert resume reviewer and ATS (Applicant Tracking System) specialist.
Given a student's resume text and target role, you will:
1. Score the resume on ATS compatibility (0-100)
2. Identify missing critical keywords for the target role
3. Evaluate structure, formatting, and content quality
4. Suggest specific improvements to each section
5. Provide a rewritten version of the summary/objective section

Always return a structured JSON response."""

AGENT_TYPE = "resume_analysis"


async def run_resume_analysis_agent(resume_data: dict) -> dict:
    """
    resume_data = {
        "name": str,
        "resume_text": str,
        "target_role": str,
        "cgpa": float,
        "skills": [str],
    }
    """
    gateway = get_llm_gateway()

    resume_text = resume_data.get("resume_text", "")
    target_role = resume_data.get("target_role", "Software Engineer")

    # Truncate very long resumes
    if len(resume_text) > 4000:
        resume_text = resume_text[:4000] + "\n[... truncated ...]"

    user_message = f"""Analyze the following resume for a {target_role} position:

Student Name: {resume_data.get('name', 'Student')}
Target Role: {target_role}
CGPA: {resume_data.get('cgpa', 'N/A')}

Resume Content:
---
{resume_text}
---

Provide a comprehensive resume analysis in this JSON format:
{{
  "ats_score": <0-100>,
  "overall_rating": "<Excellent/Good/Average/Poor/Needs Major Work>",
  "section_scores": {{
    "contact_info": <0-10>,
    "summary_objective": <0-10>,
    "education": <0-10>,
    "experience": <0-10>,
    "skills": <0-10>,
    "projects": <0-10>,
    "certifications": <0-10>,
    "formatting": <0-10>
  }},
  "strengths": ["..."],
  "critical_issues": ["..."],
  "improvements": [
    {{
      "section": "...",
      "issue": "...",
      "suggestion": "...",
      "priority": "High/Medium/Low"
    }}
  ],
  "missing_keywords": ["..."],
  "keywords_present": ["..."],
  "missing_sections": ["..."],
  "rewritten_summary": "...",
  "quantification_suggestions": ["..."],
  "action_verb_suggestions": ["..."],
  "overall_feedback": "..."
}}"""

    request = LLMRequest(
        messages=[{"role": "user", "content": user_message}],
        system_prompt=SYSTEM_PROMPT,
        model="auto",
        max_tokens=2500,
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

    # Human-in-the-loop: flag if ATS score is very low (needs counsellor review)
    ats_score = result.get("ats_score", 100)
    hitl_required = ats_score < 40

    return {
        "agent_type": AGENT_TYPE,
        "analysis": result,
        "hitl_required": hitl_required,
        "tokens_used": llm_response.input_tokens + llm_response.output_tokens,
        "cost_usd": llm_response.cost_usd,
        "model": llm_response.model,
        "latency_ms": llm_response.latency_ms,
    }
