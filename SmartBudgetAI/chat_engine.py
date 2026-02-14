from datetime import datetime, timedelta
from SmartBudgetAI.parser import parse_message
from SmartBudgetAI.executor import execute_intent
from SmartBudgetAI.memory import get_active_loan_items
from SmartBudgetAI.db import close_memory_fact, add_reminder, get_due_reminders
from SmartBudgetAI.intent_schema import ParsedIntent
# Import the new functions from your updated llm_fallback
from SmartBudgetAI.llm_fallback import llm_fallback_parse, chat_with_persona

SESSION_CONTEXT = {}

# State Constants
STATE_IDLE = "IDLE"
STATE_CLARIFY_INTENT = "CLARIFY_INTENT"
STATE_CONFIRM_ACTION = "CONFIRM_ACTION"
STATE_SELECT_LOAN = "SELECT_LOAN"

def handle_user_message(text, user_id=1):
    original_text = text.strip()
    text_lower = original_text.lower()
    
    # ==================================================
    # 1️⃣ PASSIVE REMINDER CHECK (The "2 Days Ago" Logic)
    # ==================================================
    # This runs silently every time the user messages.
    due_reminders = get_due_reminders(user_id)
    # If there are reminders, we prep a string to prepend to the final answer
    reminder_text = ("\n\n".join(due_reminders) + "\n\n---\n") if due_reminders else ""

    # ==================================================
    # 2️⃣ CONTEXT SETUP & GLOBAL CANCEL
    # ==================================================
    if user_id not in SESSION_CONTEXT:
        SESSION_CONTEXT[user_id] = { "state": STATE_IDLE, "data": {} }
    ctx = SESSION_CONTEXT[user_id]
    state = ctx["state"]

    if text_lower in ["cancel", "stop", "forget it", "nevermind"] and state != STATE_IDLE:
        ctx["state"] = STATE_IDLE
        ctx["data"] = {}
        return reminder_text + "Bet, cancelled. 👍"

    # ==================================================
    # 3️⃣ STATE MACHINE (The "Smart Agent" Logic)
    # ==================================================
    
    # --- A. CLOSING LOANS (Multiple Options) ---
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
            return reminder_text + f"Closed the loan with {selected_loan['entity']}."
        else:
            return reminder_text + "I didn't catch which one. Say 'first' or the name."

    # --- B. CLARIFYING INTENT (Lent vs Received) ---
    if state == STATE_CLARIFY_INTENT:
        pending_intent = ctx["data"]["pending_intent"]
        
        if any(w in text_lower for w in ["lent", "gave", "lend", "given"]):
            pending_intent.intent = "loan_given"
        elif any(w in text_lower for w in ["got", "received", "paid", "repaid"]):
            pending_intent.intent = "loan_received"
        else:
            # Smart Fallback: If they chat instead of answering
            return reminder_text + chat_with_persona(original_text) + "\n\n_(Still waiting: Did you LEND money or RECEIVE it?)_"

        ctx["data"]["pending_intent"] = pending_intent
        ctx["state"] = STATE_CONFIRM_ACTION
        
        action_verb = "lend" if pending_intent.intent == "loan_given" else "receive repayment from"
        return reminder_text + f"Got it. Record that you {action_verb} {pending_intent.entity} ${pending_intent.amount:.0f}?"

    # --- C. SMART CONFIRMATION (Handles Yes/No AND Corrections) ---
    if state == STATE_CONFIRM_ACTION:
        # 1. Explicit Confirmation
        if text_lower in ["yes", "yeah", "yep", "sure", "correct", "bet", "ok"]:
            pending_intent = ctx["data"]["pending_intent"]
            response = execute_intent(user_id, pending_intent)
            ctx["state"] = STATE_IDLE
            ctx["data"] = {}
            return reminder_text + response
        
        # 2. Explicit Rejection
        elif text_lower in ["no", "nah", "nope", "wrong"]:
            ctx["state"] = STATE_IDLE
            ctx["data"] = {}
            return reminder_text + "Cancelled. 👍"

        # 3. Handle Missing Name / Corrections
        pending = ctx["data"]["pending_intent"]
        # If the user input is short (likely a name) OR the current entity is None
        if (pending.entity is None or pending.entity == "None") and len(original_text.split()) < 5:
            # Heuristic: Assume the input IS the name
            new_name = original_text
            for prefix in ["it is ", "his name is ", "name is ", "it's "]:
                if text_lower.startswith(prefix):
                    new_name = original_text[len(prefix):].strip()
            
            # Update the name
            pending.entity = new_name.title()
            ctx["data"]["pending_intent"] = pending
            
            verb = "lend" if pending.intent == "loan_given" else "receive repayment from"
            return reminder_text + f"Got it. Do you want to record that you {verb} **{pending.entity}** ${pending.amount:.0f}?"

        # 4. Context Switch (Chit-Chat)
        # If we are here, the user said something that isn't Yes/No/Name.
        # We answer with the persona, but KEEP THE STATE active.
        persona_reply = chat_with_persona(original_text)
        
        verb = "lend" if pending.intent == "loan_given" else "receive repayment from"
        name_display = pending.entity if pending.entity else "???"
        
        return (
            f"{reminder_text}{persona_reply}\n\n"
            f"_(BTW, still pending: Did you {verb} **{name_display}** ${pending.amount:.0f}? Say 'Yes' or give me the name.)_"
        )

    # ==================================================
    # 4️⃣ NEW: "Remind Me" Command
    # ==================================================
    if "remind me in" in text_lower and "days" in text_lower:
        try:
            parts = text_lower.split("remind me in")[1].strip()
            days_str = parts.split("days")[0].strip()
            days = int(days_str)
            message_body = original_text.split("to", 1)[1].strip() if "to" in original_text else "check this"
            
            future_time = (datetime.now() + timedelta(days=days)).isoformat()
            add_reminder(user_id, message_body, future_time)
            return reminder_text + f"Got u. I'll remind you to **{message_body}** in {days} days. 📅"
        except:
            pass # Parsing failed, let LLM try or Party Mode handle it

    # ==================================================
    # 5️⃣ MAIN ROUTER (Idle State)
    # ==================================================
    
    # A. Check for specific commands
    if "close loan" in text_lower:
        loans = get_active_loan_items(user_id)
        if not loans:
            return reminder_text + "I don’t see any active loans to close. 🤷‍♂️"
        if len(loans) == 1:
            close_memory_fact(loans[0]["id"])
            return reminder_text + f"Closed the loan with {loans[0]['entity']}."
        
        ctx["state"] = STATE_SELECT_LOAN
        ctx["data"]["loan_options"] = loans
        msg = "You have multiple active loans. Which one?\n"
        for i, loan in enumerate(loans, 1):
            msg += f"{i}. {loan['entity']} (${loan['remaining_amount']:.0f})\n"
        return reminder_text + msg

    # B. Try Regex (Fast)
    parsed = parse_message(original_text)

    # C. Try LLM (TinyLlama) if Regex is unsure
    if parsed.confidence < 0.6:
        llm_result = llm_fallback_parse(original_text)
        # Only trust LLM if it found a financial intent
        if llm_result.intent in ["loan_given", "loan_received", "query_debts"]:
            parsed = llm_result

    # D. Decision: Money or Party?
    # This check decides if we use Financial Logic or Persona Chat
    is_financial = (parsed.confidence > 0.6) or (getattr(parsed, "needs_confirmation", False))
    
    if is_financial:
        # --- BUSINESS MODE 💼 ---
        if getattr(parsed, "needs_confirmation", False):
            ctx["state"] = STATE_CLARIFY_INTENT
            ctx["data"]["pending_intent"] = parsed
            
            if parsed.intent in ["loan_given", "loan_received"]:
                 ctx["state"] = STATE_CONFIRM_ACTION
                 # Check if we are missing the name
                 if parsed.entity is None or parsed.entity == "None":
                     return reminder_text + f"I found the amount (${parsed.amount}), but who is this for?"
                 
                 verb = "lend" if parsed.intent == "loan_given" else "receive repayment from"
                 return reminder_text + f"Do you want to record that you {verb} {parsed.entity} ${parsed.amount:.0f}?"
            
            return reminder_text + f"Did you lend {parsed.entity} ${parsed.amount:.0f} or did they repay you?"

        # High confidence match
        if parsed.confidence >= 0.8:
            ctx["state"] = STATE_CONFIRM_ACTION
            ctx["data"]["pending_intent"] = parsed
            verb = "lend" if parsed.intent == "loan_given" else "receive repayment from"
            return reminder_text + f"Do you want to record that you {verb} {parsed.entity} ${parsed.amount:.0f}?"
            
        return reminder_text + execute_intent(user_id, parsed)

    else:
        # --- PARTY MODE 🎉 ---
        # CRITICAL: This else block catches "Hi", "Hello", etc.
        return reminder_text + chat_with_persona(original_text)