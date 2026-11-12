"""
Guardrails — input sanitization, output validation, and policy enforcement.
"""
import re
from typing import Optional


# ─── Prompt Injection Defense ─────────────────────────────────────────────────

INJECTION_PATTERNS = [
    r"ignore (all |previous |above )?instructions",
    r"forget (everything|all|your instructions)",
    r"you are now",
    r"act as (a |an )?(different|new|evil|unrestricted)",
    r"DAN (mode|prompt)",
    r"jailbreak",
    r"do anything now",
    r"<\|system\|>",
    r"\[INST\].*override",
]


def sanitize_input(text: str) -> tuple[str, bool]:
    """
    Sanitize user input for prompt injection attempts.
    Returns (cleaned_text, was_flagged).
    """
    text_lower = text.lower()
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, text_lower):
            return text, True
    # Strip any embedded system-like markers
    cleaned = re.sub(r"<\|.*?\|>", "", text)
    return cleaned, False


# ─── PII Detection ────────────────────────────────────────────────────────────

PII_PATTERNS = {
    "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
    "phone": r"\b(?:\+91|0)?[6-9]\d{9}\b",
    "aadhaar": r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}\b",
    "pan": r"\b[A-Z]{5}[0-9]{4}[A-Z]\b",
}


def redact_pii(text: str) -> str:
    """Replace PII patterns with redacted placeholders."""
    for label, pattern in PII_PATTERNS.items():
        text = re.sub(pattern, f"[{label.upper()}_REDACTED]", text, flags=re.IGNORECASE)
    return text


# ─── Output Validators ────────────────────────────────────────────────────────

def validate_ats_score(score: any) -> bool:
    """ATS score must be a number between 0 and 100."""
    try:
        s = float(score)
        return 0 <= s <= 100
    except (TypeError, ValueError):
        return False


def validate_agent_output(output: dict, agent_type: str) -> tuple[bool, list[str]]:
    """
    Validate that an agent's output contains required fields.
    Returns (is_valid, list_of_issues).
    """
    issues = []

    if not isinstance(output, dict):
        return False, ["Output is not a dictionary"]

    required_fields = {
        "academic_performance": ["academic_health_score", "placement_risk_level"],
        "skill_gap": ["missing_critical_skills", "overall_readiness_score"],
        "career_recommendation": ["top_recommendations"],
        "learning_path": ["phases"],
        "resume_analysis": ["ats_score", "improvements"],
        "interview_prep": ["questions"],
    }

    for field in required_fields.get(agent_type, []):
        if field not in output:
            issues.append(f"Missing required field: {field}")

    return len(issues) == 0, issues


# ─── Content Safety ────────────────────────────────────────────────────────────

HARMFUL_PATTERNS = [
    r"\b(suicide|self.harm|kill yourself)\b",
    r"\b(illegal|fraud|cheat)\b",
]


def is_content_safe(text: str) -> bool:
    """Basic harmful content check."""
    text_lower = text.lower()
    for pattern in HARMFUL_PATTERNS:
        if re.search(pattern, text_lower):
            return False
    return True
