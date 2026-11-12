"""
LLM Gateway — unified interface for IBM watsonx, OpenAI, and Anthropic.
Falls back to demo mode if no API keys are configured.
"""
import time
import json
from typing import Optional
from dataclasses import dataclass, field
import structlog

logger = structlog.get_logger(__name__)


@dataclass
class LLMRequest:
    messages: list
    model: str = "auto"
    max_tokens: int = 2048
    temperature: float = 0.3
    system_prompt: Optional[str] = None
    metadata: dict = field(default_factory=dict)


@dataclass
class LLMResponse:
    content: str
    model: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    latency_ms: int
    provider: str


AGENT_PROVIDER_MAP = {
    "academic_performance": "ibm_watsonx",
    "skill_gap": "openai",
    "career_recommendation": "anthropic",
    "learning_path": "openai",
    "resume_analysis": "anthropic",
    "interview_prep": "ibm_watsonx",
    "supervisor": "openai",
}

PROVIDER_MODELS = {
    "ibm_watsonx": "watsonx/ibm/granite-13b-chat-v2",
    "openai": "openai/gpt-4o",
    "anthropic": "anthropic/claude-3-5-sonnet-20241022",
}

# Demo responses per agent type for when no API keys are set
DEMO_RESPONSES = {
    "academic_performance": json.dumps({
        "academic_health_score": 7,
        "cgpa_assessment": "Good",
        "cgpa_band": "6-8",
        "semester_trend": "Stable",
        "weak_subjects": [{"subject": "Mathematics", "percentage": 45, "severity": "moderate", "improvement_tip": "Practice past papers daily and seek tutoring for key topics."}],
        "strong_subjects": ["Computer Science", "English"],
        "placement_risk_level": "Low",
        "placement_cgpa_eligible": True,
        "key_recommendations": ["Focus on Mathematics improvement", "Build more projects", "Start placement preparation 6 months early"],
        "priority_focus_areas": ["Mathematics", "Data Structures"],
        "overall_summary": "The student shows a good academic profile with some scope for improvement in quantitative subjects. Overall placement eligibility is strong."
    }),
    "skill_gap": json.dumps({
        "target_role": "Software Engineer",
        "required_skills": [
            {"skill": "Data Structures & Algorithms", "category": "technical", "importance": "critical", "current_proficiency": "beginner", "gap_severity": "major", "estimated_learning_weeks": 8, "learning_approach": "Practice on LeetCode daily"},
            {"skill": "System Design", "category": "technical", "importance": "high", "current_proficiency": "none", "gap_severity": "major", "estimated_learning_weeks": 6, "learning_approach": "Study Grokking System Design"},
            {"skill": "Python/Java", "category": "technical", "importance": "critical", "current_proficiency": "intermediate", "gap_severity": "minor", "estimated_learning_weeks": 2, "learning_approach": "Build 2-3 portfolio projects"}
        ],
        "missing_critical_skills": ["Data Structures & Algorithms", "System Design"],
        "missing_high_priority_skills": ["SQL", "REST APIs", "Git"],
        "skills_to_improve": [{"skill": "Python", "current": "intermediate", "target": "advanced", "suggestion": "Build production-grade projects"}],
        "existing_strengths": ["Communication", "Team Work", "Basic Programming"],
        "overall_readiness_score": 42,
        "readiness_level": "Developing",
        "estimated_total_preparation_weeks": 16,
        "priority_action_items": ["Start DSA practice on LeetCode", "Complete System Design course", "Build 2 full-stack projects", "Contribute to open source"]
    }),
    "career_recommendation": json.dumps({
        "top_recommendations": [
            {"rank": 1, "role": "Software Engineer", "industry": "Technology", "match_score": 78, "match_reasons": ["Strong programming foundation", "Good academic record"], "key_skills_required": ["DSA", "System Design", "Python"], "skills_already_have": ["Python", "Communication"], "skills_to_develop": ["System Design", "DSA"], "average_salary_inr": "₹6-15 LPA", "growth_outlook": "Excellent", "entry_level_titles": ["Junior Developer", "Associate SWE"], "top_companies": ["TCS", "Infosys", "Wipro", "Startups"], "career_trajectory": "SWE → Senior SWE → Tech Lead → Engineering Manager"},
            {"rank": 2, "role": "Data Analyst", "industry": "Analytics", "match_score": 72, "match_reasons": ["Good with numbers", "Python skills"], "key_skills_required": ["SQL", "Python", "Power BI"], "skills_already_have": ["Python", "Excel"], "skills_to_develop": ["SQL", "Power BI"], "average_salary_inr": "₹5-12 LPA", "growth_outlook": "Good", "entry_level_titles": ["Junior Analyst"], "top_companies": ["Deloitte", "Accenture", "MNCs"], "career_trajectory": "Analyst → Senior Analyst → Data Scientist → Analytics Manager"},
        ],
        "not_recommended_roles": [{"role": "Hardware Engineer", "reason": "Profile is software-focused"}],
        "overall_career_profile": "Well-suited for software and analytics roles in the IT sector.",
        "immediate_next_steps": ["Build a project portfolio", "Get AWS/Azure certification", "Practice DSA for interviews"],
        "long_term_vision": "Progress to senior technical roles or transition to product management within 5-7 years."
    }),
    "learning_path": json.dumps({
        "target_role": "Software Engineer",
        "total_duration_weeks": 16,
        "phases": [
            {"phase_number": 1, "phase_name": "Foundation", "weeks": "1-4", "objectives": ["Master Python", "Learn basic DSA"], "topics": ["Python OOP", "Arrays", "Linked Lists", "Stacks"], "courses": [{"title": "Python for Everybody", "platform": "Coursera", "url_hint": "coursera.org/specializations/python", "duration_hours": 40, "cost": "Free", "priority": "Must"}], "projects": [{"title": "CLI Task Manager", "description": "Build a command-line task manager in Python", "skills_practiced": ["Python", "OOP"]}], "milestone": "Complete 50 LeetCode easy problems", "assessment": "Build and push a Python project to GitHub"},
            {"phase_number": 2, "phase_name": "Core CS & DSA", "weeks": "5-10", "objectives": ["Master DSA", "Learn SQL", "REST APIs"], "topics": ["Trees", "Graphs", "Dynamic Programming", "SQL Joins"], "courses": [{"title": "Data Structures & Algorithms", "platform": "Coursera", "url_hint": "coursera.org/specializations/data-structures-algorithms", "duration_hours": 100, "cost": "Free", "priority": "Must"}], "projects": [{"title": "Full Stack Web App", "description": "Build a CRUD app with Python backend and React frontend", "skills_practiced": ["Python", "SQL", "REST", "React"]}], "milestone": "Complete 100 LeetCode problems", "assessment": "Deploy a web app"},
            {"phase_number": 3, "phase_name": "Interview Prep", "weeks": "11-16", "objectives": ["System Design basics", "Mock interviews"], "topics": ["System Design patterns", "Behavioral interviews", "Resume polish"], "courses": [{"title": "Grokking System Design", "platform": "educative.io", "url_hint": "educative.io/courses/grokking-system-design-interview", "duration_hours": 15, "cost": "Paid", "priority": "Must"}], "projects": [{"title": "Portfolio Website", "description": "Showcase all projects with a professional portfolio site", "skills_practiced": ["HTML", "CSS", "Deployment"]}], "milestone": "Complete 5 mock interviews", "assessment": "Apply to 20 companies"}
        ],
        "weekly_time_commitment_hours": 15,
        "recommended_resources": [{"type": "YouTube", "name": "freeCodeCamp", "topic": "Full Stack Development"}, {"type": "Book", "name": "Cracking the Coding Interview", "topic": "DSA & Interviews"}],
        "mock_interview_schedule": "Start mock interviews from week 12, 2 per week",
        "success_metrics": ["100 LeetCode problems solved", "3 deployed projects", "Resume score > 75%", "Job offer received"],
        "final_project_idea": "Build an AI-powered task management app with Python backend, React frontend, and deployment on cloud"
    }),
    "resume_analysis": json.dumps({
        "ats_score": 62,
        "overall_rating": "Average",
        "section_scores": {"contact_info": 8, "summary_objective": 5, "education": 8, "experience": 4, "skills": 7, "projects": 6, "certifications": 3, "formatting": 7},
        "strengths": ["Clear contact information", "Good education section", "Relevant skills listed"],
        "critical_issues": ["No quantified achievements", "Missing action verbs in project descriptions", "No certifications listed"],
        "improvements": [{"section": "Summary", "issue": "Generic summary", "suggestion": "Write a 2-3 line targeted summary mentioning your specific skills and career goal", "priority": "High"}, {"section": "Projects", "issue": "No metrics", "suggestion": "Add numbers: 'Increased performance by 40%' instead of 'Improved performance'", "priority": "High"}],
        "missing_keywords": ["Agile", "Git", "REST API", "Cloud", "CI/CD"],
        "keywords_present": ["Python", "SQL", "Java"],
        "missing_sections": ["Certifications", "Achievements"],
        "rewritten_summary": "Computer Science graduate with strong Python and Java skills, seeking a Software Engineer role. Built 3 full-stack projects. Passionate about building scalable, user-centric applications.",
        "quantification_suggestions": ["Add numbers of users, performance gains, or lines of code to project descriptions"],
        "action_verb_suggestions": ["Use: Developed, Implemented, Designed, Optimized, Led, Built instead of weak verbs"],
        "overall_feedback": "Your resume has a good structure but needs stronger language, quantified achievements, and targeted keywords. Adding certifications would significantly improve your ATS score."
    }),
    "interview_prep": json.dumps({
        "role": "Software Engineer",
        "questions": [
            {"id": 1, "type": "Technical", "difficulty": "Easy", "question": "What is the difference between a list and a tuple in Python?", "topic": "Python", "expected_duration_minutes": 3, "key_evaluation_criteria": ["Mutability", "Use cases", "Performance"], "hint": "Focus on mutability"},
            {"id": 2, "type": "Technical", "difficulty": "Medium", "question": "Explain the time complexity of common sorting algorithms.", "topic": "DSA", "expected_duration_minutes": 5, "key_evaluation_criteria": ["Best/Worst/Average case", "Comparison vs non-comparison sorts"], "hint": "Mention QuickSort, MergeSort, HeapSort"},
            {"id": 3, "type": "System Design", "difficulty": "Hard", "question": "How would you design a URL shortener like bit.ly?", "topic": "System Design", "expected_duration_minutes": 15, "key_evaluation_criteria": ["Scalability", "Database choice", "Hashing strategy"], "hint": "Think about hash generation, storage, and cache"},
            {"id": 4, "type": "Behavioral", "difficulty": "Easy", "question": "Tell me about a challenging project you worked on.", "topic": "Behavioral", "expected_duration_minutes": 5, "key_evaluation_criteria": ["STAR method", "Problem-solving", "Impact"], "hint": "Use STAR: Situation, Task, Action, Result"},
            {"id": 5, "type": "HR", "difficulty": "Easy", "question": "Where do you see yourself in 5 years?", "topic": "HR", "expected_duration_minutes": 3, "key_evaluation_criteria": ["Career clarity", "Ambition", "Alignment with role"], "hint": "Align your goals with the company's growth"}
        ],
        "interview_tips": ["Research the company before the interview", "Prepare 3-5 questions to ask the interviewer", "Practice coding on a whiteboard or shared screen"],
        "preparation_advice": "Focus on DSA fundamentals, system design patterns, and behavioral answers using the STAR method."
    }),
    "evaluate_answer": json.dumps({
        "score": 7,
        "confidence": 0.85,
        "grade": "Good",
        "accuracy_score": 7,
        "completeness_score": 6,
        "clarity_score": 8,
        "depth_score": 6,
        "strengths": ["Clear and concise explanation", "Correct key points covered"],
        "weaknesses": ["Could add more examples", "Missing edge case discussion"],
        "detailed_feedback": "Good answer overall. You covered the main concepts correctly. To improve, add a practical example and discuss edge cases.",
        "model_answer": "A comprehensive answer would cover: the core concept, practical use cases, edge cases, and trade-offs. For example...",
        "improvement_tips": ["Study more examples from real-world applications", "Practice explaining concepts out loud", "Read official documentation"],
        "follow_up_question": "Can you give a real-world example where you applied this concept?"
    }),
}


class LLMGateway:
    def __init__(self):
        self._litellm_available = False
        self._setup_providers()

    def _setup_providers(self):
        from app.config import get_settings
        settings = get_settings()
        if not settings.openai_api_key and not settings.anthropic_api_key and not settings.ibm_api_key:
            logger.warning("no_llm_keys", msg="No LLM API keys set. Running in demo mode with pre-built responses.")
            return

        import os
        os.environ["OPENAI_API_KEY"] = settings.openai_api_key
        os.environ["ANTHROPIC_API_KEY"] = settings.anthropic_api_key
        os.environ["WATSONX_API_KEY"] = settings.ibm_api_key
        os.environ["WATSONX_URL"] = settings.ibm_url
        os.environ["WATSONX_PROJECT_ID"] = settings.ibm_project_id

        try:
            import litellm
            self._litellm_available = bool(settings.openai_api_key or settings.anthropic_api_key)
        except ImportError:
            pass

    def get_model_for_agent(self, agent_type: str) -> str:
        provider_key = AGENT_PROVIDER_MAP.get(agent_type, "openai")
        return PROVIDER_MODELS.get(provider_key, "openai/gpt-4o")

    async def complete(self, request: LLMRequest, agent_type: str = "default") -> LLMResponse:
        start_time = time.time()

        if self._litellm_available:
            return await self._litellm_complete(request, agent_type, start_time)

        # Demo mode — return pre-built responses
        return self._demo_complete(agent_type, start_time)

    async def _litellm_complete(self, request: LLMRequest, agent_type: str, start_time: float) -> LLMResponse:
        import litellm
        messages = request.messages.copy()
        if request.system_prompt:
            messages = [{"role": "system", "content": request.system_prompt}] + messages

        model = request.model if request.model != "auto" else self.get_model_for_agent(agent_type)

        try:
            response = await litellm.acompletion(
                model=model,
                messages=messages,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
            )
        except Exception as e:
            logger.warning("litellm_fallback", error=str(e))
            return self._demo_complete(agent_type, start_time)

        latency_ms = int((time.time() - start_time) * 1000)
        usage = response.usage
        try:
            cost = litellm.completion_cost(completion_response=response)
        except Exception:
            cost = 0.0

        provider = model.split("/")[0]
        return LLMResponse(
            content=response.choices[0].message.content,
            model=model,
            input_tokens=usage.prompt_tokens,
            output_tokens=usage.completion_tokens,
            cost_usd=cost,
            latency_ms=latency_ms,
            provider=provider,
        )

    def _demo_complete(self, agent_type: str, start_time: float) -> LLMResponse:
        """Return a pre-built demo response when no API keys are configured."""
        content = DEMO_RESPONSES.get(agent_type, DEMO_RESPONSES.get("academic_performance", "{}"))
        latency_ms = int((time.time() - start_time) * 1000)
        return LLMResponse(
            content=content,
            model="demo/mock-model",
            input_tokens=100,
            output_tokens=300,
            cost_usd=0.0,
            latency_ms=latency_ms,
            provider="demo",
        )


_gateway: Optional[LLMGateway] = None


def get_llm_gateway() -> LLMGateway:
    global _gateway
    if _gateway is None:
        _gateway = LLMGateway()
    return _gateway
