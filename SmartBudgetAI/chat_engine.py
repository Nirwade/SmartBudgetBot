from SmartBudgetAI.parser import parse_message
from SmartBudgetAI.executor import execute_intent
from SmartBudgetAI.memory import get_active_loan_items
from SmartBudgetAI.db import close_memory_fact
from SmartBudgetAI.intent_schema import ParsedIntent
from SmartBudgetAI.llm_fallback import llm_fallback_parse

SESSION_CONTEXT = {}

# State Constants
STATE_IDLE = "IDLE"
STATE_CLARIFY_INTENT = "CLARIFY_INTENT"
STATE_CONFIRM_ACTION = "CONFIRM_ACTION"
STATE_SELECT_LOAN = "SELECT_LOAN"

def handle_user_message(text, user_id=1):
    # FIX: Keep original for parser (Names need capitals), use lower for commands
    original_text = text.strip()
    text_lower = original_text.lower()

    if user_id not in SESSION_CONTEXT:
        SESSION_CONTEXT[user_id] = {
            "state": STATE_IDLE,
            "data": {} 
        }

    ctx = SESSION_CONTEXT[user_id]
    state = ctx["state"]

    # ==================================================
    # 0️⃣ GLOBAL ABORT
    # ==================================================
    if text_lower in ["no", "cancel", "stop", "forget it"] and state != STATE_IDLE:
        ctx["state"] = STATE_IDLE
        ctx["data"] = {}
        return "Okay 👍 please rephrase what you meant."

    # ==================================================
    # 1️⃣ STATE: SELECT LOAN (Closing Flow)
    # ==================================================
    if state == STATE_SELECT_LOAN:
        options = ctx["data"].get("loan_options", [])
        selected_loan = None
        
        if "first" in text_lower or "1" in text_lower:
            selected_loan = options[0]
        elif "second" in text_lower or "2" in text_lower:
            if len(options) > 1: selected_loan = options[1]
        else:
            for loan in options:
                if loan["entity"].lower() in text_lower:
                    selected_loan = loan
                    break
        
        if selected_loan:
            close_memory_fact(selected_loan["id"])
            ctx["state"] = STATE_IDLE
            ctx["data"] = {}
            return f"Closed the loan with {selected_loan['entity']}."
        else:
            return "I didn't catch which one. Please say 'first' or the name."

    # ==================================================
    # 2️⃣ STATE: CLARIFY INTENT ("John 300" -> "Lent or Received?")
    # ==================================================
    if state == STATE_CLARIFY_INTENT:
        pending_intent = ctx["data"]["pending_intent"]
        
        # We rely on the pending_intent for entity/amount, 
        # and current text ONLY for intent direction.
        if "lent" in text_lower or "gave" in text_lower or "lend" in text_lower:
            pending_intent.intent = "loan_given"
        elif "got" in text_lower or "received" in text_lower or "paid" in text_lower:
            pending_intent.intent = "loan_received"
        else:
            return "Did you lend the money or receive it back?"

        # Transition to Confirmation
        ctx["data"]["pending_intent"] = pending_intent
        ctx["state"] = STATE_CONFIRM_ACTION
        
        action_verb = "lend" if pending_intent.intent == "loan_given" else "receive"
        return f"Got it. You want to record that you {action_verb} {pending_intent.entity} ${pending_intent.amount:.0f}. Correct?"

    # ==================================================
    # 3️⃣ STATE: CONFIRM ACTION ("Correct?" -> "Yes")
    # ==================================================
    if state == STATE_CONFIRM_ACTION:
        if text_lower in ["yes", "yeah", "yep", "sure", "correct"]:
            pending_intent = ctx["data"]["pending_intent"]
            response = execute_intent(user_id, pending_intent)
            ctx["state"] = STATE_IDLE
            ctx["data"] = {}
            return response
        else:
            return "Please reply 'yes' to confirm or 'no' to cancel."

    # ==================================================
    # 4️⃣ STATE: IDLE (New Commands)
    # ==================================================
    if "close loan" in text_lower:
        loans = get_active_loan_items(user_id)
        if not loans:
            return "I don’t see any active loans 🙂"
        
        if len(loans) == 1:
            close_memory_fact(loans[0]["id"])
            return f"Closed the loan with {loans[0]['entity']}."
        
        ctx["state"] = STATE_SELECT_LOAN
        ctx["data"]["loan_options"] = loans
        msg = "You have multiple active loans. Which one?\n"
        for i, loan in enumerate(loans, 1):
            msg += f"{i}. {loan['entity']} (${loan['remaining_amount']:.0f})\n"
        return msg

    # --- INTELLIGENT PARSING ---

    # 1. Try REGEX Parser first (Fast, Precise, Rules-based)
    parsed = parse_message(original_text)

    # 2. DECISION: If Regex is failing (0.0) or just guessing (Ambiguous < 0.6),
    # let the LLM try to understand the sentence.
    if parsed.confidence < 0.6:
        llm_result = llm_fallback_parse(original_text)
        
        # Only accept LLM if it found a specific intent (loan_given/received)
        # If LLM also returns 'clarify', we stick with what we have or generic fallback
        if llm_result.intent in ["loan_given", "loan_received"]:
            parsed = llm_result

    # Case A: Ambiguous (Regex "John 300") OR LLM Guess (Always needs confirm)
    if getattr(parsed, "needs_confirmation", False):
        ctx["state"] = STATE_CLARIFY_INTENT
        ctx["data"]["pending_intent"] = parsed
        
        # If it's the LLM, it usually identifies the intent but wants confirmation
        if parsed.intent in ["loan_given", "loan_received"]:
             # Skip straight to confirmation state if LLM is pretty sure about direction
             ctx["state"] = STATE_CONFIRM_ACTION
             verb = "lend" if parsed.intent == "loan_given" else "receive repayment from"
             return f"Do you want to record that you {verb} {parsed.entity} ${parsed.amount:.0f}?"
        
        # Standard Ambiguity (Regex: "John 300")
        return (
            f"Did you lend {parsed.entity} ${parsed.amount:.0f}, "
            f"or did {parsed.entity} repay you ${parsed.amount:.0f}?"
        )

    # Case B: High Confidence (Soft Confirm)
    # We enforce a "Yes/No" confirmation step for all financial writes
    if parsed.confidence >= 0.8 and parsed.amount is not None:
        ctx["state"] = STATE_CONFIRM_ACTION
        ctx["data"]["pending_intent"] = parsed
        verb = "lend" if parsed.intent == "loan_given" else "receive repayment from"
        return f"Do you want to record that you {verb} {parsed.entity} ${parsed.amount:.0f}?"

    # Case C: Direct Execution (Queries, etc.)
    return execute_intent(user_id, parsed)