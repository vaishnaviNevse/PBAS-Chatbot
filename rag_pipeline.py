from langchain_community.llms import Ollama
from database import (
    get_user_stats,
    get_rules_by_activity_and_level,
    get_promotion_requirements,
    get_audit_reason,
    save_message,
    update_session_category,
    create_session_if_not_exists
)
from embeddings import semantic_rule_search
from memory import build_memory


# ---------------- LOAD LOCAL LLM ----------------
llm = Ollama(model="tinyllama")


# ---------------- SYSTEM GUARDRAIL ----------------
SYSTEM_GUARDRAIL = """
You are VERO Academic Assistant.

STRICT RULES:
- Always cite PBAS Rule IDs when giving scores.
- Never guess points.
- Use USER PROFILE data for personalization.
- Explain document statuses in human-friendly language.
- If rule not found, say you cannot find it in PBAS documents.
- Only answer PBAS, promotion, appraisal, or document queries.
"""


# ---------------- SESSION CATEGORY DETECTION ----------------
def detect_category(message: str) -> str:
    msg = message.lower()

    if "upload" in msg or "certificate" in msg or "document" in msg:
        return "upload_help"
    if "promotion" in msg or "eligible" in msg:
        return "promotion"
    if "score" in msg or "points" in msg or "rule" in msg:
        return "scoring"
    return "general"


# ---------------- MAIN PIPELINE FUNCTION ----------------
def ask_pbas_bot(question: str, user_id: int, session_id: str):

    # ✅ Ensure session exists in DB
    create_session_if_not_exists(session_id, user_id)

    # 1️⃣ Save user message
    save_message(session_id, "user", question, user_id)

    # 2️⃣ Guardrail check
    allowed_keywords = ["pbas", "score", "category", "promotion", "document", "upload", "points", "rule"]
    if not any(word in question.lower() for word in allowed_keywords):
        reply = "I am the VERO Academic Assistant. I can only assist with appraisal and document queries."
        save_message(session_id, "assistant", reply, user_id)
        return reply

    # 3️⃣ Detect session category
    category = detect_category(question)
    update_session_category(session_id, category)

    # 4️⃣ Load conversation memory
    memory_context = build_memory(session_id)

    # 5️⃣ Fetch user profile stats
    stats = get_user_stats(user_id)

    if stats:
        academic_level = stats[3]
        total_score = stats[1]
        rank = stats[2]
    else:
        academic_level = None
        total_score = 0
        rank = None

    # 6️⃣ Promotion Logic
    promotion_info = ""
    if "promotion" in question.lower() and rank:
        required_score = get_promotion_requirements(rank)
        if required_score:
            remaining = required_score - total_score
            promotion_info = f"The user currently has {total_score} points and needs {remaining} more points for promotion."

    # 7️⃣ Semantic Rule Search
    semantic_rules = semantic_rule_search(question)

    # 8️⃣ Structured Rule Query
    activity_keywords = ["conference", "journal", "seminar", "workshop", "publication"]
    matched_keyword = next((w for w in activity_keywords if w in question.lower()), None)

    if matched_keyword and academic_level:
        structured_rules = get_rules_by_activity_and_level(matched_keyword, academic_level)
    else:
        structured_rules = []

    # 9️⃣ Audit Log Analysis
    audit_context = ""
    if any(w in question.lower() for w in ["why", "rejected", "flagged", "error"]):
        words = question.split()
        submission_id = next((w for w in words if w.isdigit()), None)

        if submission_id:
            audit_data = get_audit_reason(submission_id)
            if audit_data:
                audit_context = f"Audit Metadata Found: {audit_data}"

    # 🔟 Build Prompt
    prompt = f"""
{SYSTEM_GUARDRAIL}

USER PROFILE DATA: {stats}
PROMOTION ANALYSIS: {promotion_info}
RECENT CHAT MEMORY: {memory_context}
SEMANTIC RULE MATCHES: {semantic_rules}
STRUCTURED RULE MATCHES: {structured_rules}
AUDIT FINDINGS: {audit_context}

USER QUESTION: {question}

Provide a clear, human-friendly answer with proper PBAS rule citations.
"""

    # 1️⃣1️⃣ Call LLM
    response = llm.invoke(prompt)

    # ✅ FIX: Convert response to plain text
    if hasattr(response, "content"):
        response = response.content
    elif not isinstance(response, str):
        response = str(response)

    # 1️⃣2️⃣ Save assistant response
    save_message(session_id, "assistant", response, user_id)

    return response
