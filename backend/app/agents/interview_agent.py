"""
Interview Preparation Agent
Generates role-based interview questions and evaluates student answers.
LLM: IBM watsonx + OpenAI with Human-in-the-Loop for low-confidence evaluations.
"""
import json
from app.llm_gateway.gateway import get_llm_gateway, LLMRequest
from app.memory.chroma_store import query_similar

QUESTION_GEN_SYSTEM = """You are a senior technical interviewer at a top technology company.
Generate realistic, role-appropriate interview questions that assess both technical knowledge
and problem-solving ability. Mix different question types: conceptual, coding, system design, behavioral.
Return a structured JSON array of questions."""

EVALUATION_SYSTEM = """You are an expert interview coach evaluating student answers.
Assess the answer based on accuracy, completeness, clarity, and depth.
Provide constructive feedback and a model answer.
Be encouraging but honest. Return a structured JSON evaluation."""

AGENT_TYPE = "interview_prep"


async def generate_interview_questions(student_data: dict) -> dict:
    """
    student_data = {
        "name": str,
        "role": str,
        "skills": [str],
        "experience_level": str,  # fresher/junior/mid
        "num_questions": int,
    }
    """
    gateway = get_llm_gateway()

    role = student_data.get("role", "Software Engineer")
    num_questions = student_data.get("num_questions", 5)
    skills = student_data.get("skills", [])
    skills_str = ", ".join(skills[:8]) if skills else "Python, Data Structures, Algorithms"

    # Retrieve relevant Q&A from vector DB
    similar_qna = query_similar("interview_qna", role, n_results=3)
    qna_context = "\n".join([q["document"] for q in similar_qna]) if similar_qna else ""

    user_message = f"""Generate {num_questions} interview questions for a {role} position.

Candidate Level: {student_data.get('experience_level', 'Fresher/Entry-level')}
Key Skills: {skills_str}

Question Bank Context:
{qna_context[:600] if qna_context else "Standard interview questions for the role"}

Generate questions in this JSON format:
{{
  "role": "{role}",
  "questions": [
    {{
      "id": 1,
      "type": "Technical/Behavioral/System Design/Coding/HR",
      "difficulty": "Easy/Medium/Hard",
      "question": "...",
      "topic": "...",
      "expected_duration_minutes": <number>,
      "key_evaluation_criteria": ["..."],
      "hint": "..."
    }}
  ],
  "interview_tips": ["..."],
  "preparation_advice": "..."
}}"""

    request = LLMRequest(
        messages=[{"role": "user", "content": user_message}],
        system_prompt=QUESTION_GEN_SYSTEM,
        model="auto",
        max_tokens=2000,
        temperature=0.5,
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
        result = {"raw_questions": llm_response.content, "parse_error": True}

    return {
        "agent_type": AGENT_TYPE,
        "action": "generate_questions",
        "analysis": result,
        "tokens_used": llm_response.input_tokens + llm_response.output_tokens,
        "cost_usd": llm_response.cost_usd,
        "model": llm_response.model,
    }


async def evaluate_interview_answer(eval_data: dict) -> dict:
    """
    eval_data = {
        "role": str,
        "question": str,
        "question_type": str,
        "student_answer": str,
        "key_criteria": [str],
    }
    """
    gateway = get_llm_gateway()

    user_message = f"""Evaluate this interview answer:

Role: {eval_data.get('role', 'Software Engineer')}
Question Type: {eval_data.get('question_type', 'Technical')}
Question: {eval_data.get('question', '')}
Evaluation Criteria: {', '.join(eval_data.get('key_criteria', []))}

Student's Answer:
"{eval_data.get('student_answer', '')}"

Evaluate in this JSON format:
{{
  "score": <0-10>,
  "confidence": <0-1>,
  "grade": "<Excellent/Good/Satisfactory/Needs Improvement/Poor>",
  "accuracy_score": <0-10>,
  "completeness_score": <0-10>,
  "clarity_score": <0-10>,
  "depth_score": <0-10>,
  "strengths": ["..."],
  "weaknesses": ["..."],
  "detailed_feedback": "...",
  "model_answer": "...",
  "improvement_tips": ["..."],
  "follow_up_question": "..."
}}"""

    request = LLMRequest(
        messages=[{"role": "user", "content": user_message}],
        system_prompt=EVALUATION_SYSTEM,
        model="auto",
        max_tokens=1500,
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
        result = {"raw_evaluation": llm_response.content, "parse_error": True}

    # HITL: flag low-confidence evaluations for human review
    confidence = result.get("confidence", 1.0)
    hitl_required = confidence < 0.6

    return {
        "agent_type": AGENT_TYPE,
        "action": "evaluate_answer",
        "evaluation": result,
        "hitl_required": hitl_required,
        "tokens_used": llm_response.input_tokens + llm_response.output_tokens,
        "cost_usd": llm_response.cost_usd,
        "model": llm_response.model,
    }
