import re
from typing import List
from core.ai_service import get_ai_service

# === BRAND CONTRACT ===

BANNED_WORDS = [
    "deepseek",
    "llm",
    "large language model",
    "modelo de lenguaje",
    "openai",
    "chatgpt",
    "anthropic",
    "claude",
    "as an ai",
    "como una ia",
    "soy un modelo",
    "i am an ai",
]

# Regex patterns for minimum viability checks in Setup context
PATTERN_INVALIDATION = (
    r"(invalidaci|anula|cancel|stop|sl|pierde|rompe|por debajo de|cierre|invalidates)"
)
PATTERN_PLAN = (
    r"(plan|haría|sugiero|recomiendo|esperar|busco|entrar|target|objetivo|zona)"
)


def check_brand_safety(text: str) -> List[str]:
    """
    Checks for banned words or phrases that break immersion.
    Returns a list of violations (empty if safe).
    """
    violations = []
    text_lower = text.lower()

    for word in BANNED_WORDS:
        if word in text_lower:
            violations.append(f"Contains banned term: '{word}'")

    # Check for generic chatbot tone (heuristic)
    if "no puedo ayudarte" in text_lower or "no tengo acceso" in text_lower:
        # Context dependent, but usually bad for an "Advisor"
        violations.append("Generic chatbot refusal detected")

    return violations


def detect_intent(user_msg: str) -> str:
    """
    Heuristic to determine if user is asking for a SETUP or just GENERAL advice.
    """
    msg_lower = user_msg.lower()

    setup_keywords = [
        "entry",
        "entrada",
        "entro",
        "compro",
        "vendo",
        "long",
        "short",
        "setup",
        "trade",
        "operación",
        "stop",
        "tp",
        "sl",
        "target",
    ]

    for kw in setup_keywords:
        if kw in msg_lower:
            return "SETUP"

    return "GENERAL"


def check_minimum_viability(text: str, intent: str) -> List[str]:
    """
    Ensures the response meets the minimum value standards for the Advisor.
    """
    violations = []
    text_lower = text.lower()

    if intent == "SETUP":
        # Must have invalidation criteria
        if not re.search(PATTERN_INVALIDATION, text_lower):
            violations.append("Missing Invalidations Criteria (risk mgmt)")

        # Must have a plan or action
        if not re.search(PATTERN_PLAN, text_lower):
            violations.append("Missing Plan/Action (conditional logic)")

    return violations


def repair_response(
    original_text: str, violations: List[str], system_instruction: str
) -> str:
    """
    Uses the AI Service to rewrite the response, fixing specific violations.
    """
    print(f"[BRAND GUARD] Repairing response. Violations: {violations}")

    repair_prompt = f"""
    REWRITE the following response to fix these specific issues:
    {", ".join(violations)}
    
    original_response:
    "{original_text}"
    
    CRITICAL RULES:
    1. Act as TraderCopilot Advisor (Expert, Human-like).
    2. NEVER mention being an AI or Model.
    3. Keep value and technical details, just fix the tone/missing elements.
    4. Speak Spanish.
    """

    messages = [{"role": "user", "content": repair_prompt}]

    try:
        ai = get_ai_service()
        repaired = ai.chat(messages, system_instruction=system_instruction)

        # Double check safety (recursive safety check prevention logic needed?
        # For now, just return repaired. If it fails again, we fallback or just serve it to avoid loop.)
        return repaired
    except Exception as e:
        print(f"[BRAND GUARD] Repair failed: {e}")
        return original_text
