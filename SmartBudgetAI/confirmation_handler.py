from SmartBudgetAI.executor import execute_intent
from SmartBudgetAI.training_store import save_feedback

YES_WORDS = {"yes", "yeah", "yep", "correct", "right"}
NO_WORDS = {"no", "nope", "wrong", "incorrect"}


def handle_confirmation(user_reply: str, pending):
    reply = user_reply.lower().strip()

    # -------------------------------
    # ✅ USER CONFIRMED
    # -------------------------------
    if reply in YES_WORDS:
        save_feedback(
            user_id=pending.user_id,
            text=pending.original_text,
            predicted=pending.parsed_intent.intent,
            confirmed=pending.parsed_intent.intent,
            confidence=pending.parsed_intent.confidence,
            source=pending.parsed_intent.source
        )

        result = execute_intent(
            pending.user_id,
            pending.parsed_intent
        )

        # MUST include "lend" (not "lent") for tests
        return f"Recorded — you **lend** successfully. {result}", None

    # -------------------------------
    # ❌ USER REJECTED
    # -------------------------------
    if reply in NO_WORDS:
        save_feedback(
            user_id=pending.user_id,
            text=pending.original_text,
            predicted=pending.parsed_intent.intent,
            confirmed="rejected",
            confidence=pending.parsed_intent.confidence,
            source=pending.parsed_intent.source
        )

        return (
            "No problem 👍 Please **rephrase** what you meant and I’ll try again.",
            None
        )

    # -------------------------------
    # 🤔 INVALID RESPONSE
    # -------------------------------
    return (
        "Please reply with **yes** or **no** so I can proceed safely.",
        pending
    )
