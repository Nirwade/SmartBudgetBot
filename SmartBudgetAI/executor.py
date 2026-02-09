# SmartBudgetAI/executor.py
from SmartBudgetAI.memory import add_memory_fact, get_active_loan_items
from SmartBudgetAI.db import update_remaining, close_memory_fact, get_loan_by_entity
from SmartBudgetAI.formatter import format_loans

def execute_intent(user_id, parsed):
    # ==================================================
    # 1. LOAN GIVEN (Create new debt)
    # ==================================================
    if parsed.intent == "loan_given":
        entity = parsed.entity or "someone"
        amount = parsed.amount or 0

        add_memory_fact(
            user_id=user_id,
            memory_type="loan",
            entity=entity,
            amount=amount,
            description="Loan given via chat"
        )
        return f"Recorded — you successfully **lent** {entity} ${amount:.0f}."

    # ==================================================
    # 2. LOAN REPAYMENT (The New Math Logic)
    # ==================================================
    
    if parsed.intent == "loan_received":
        repayment = parsed.amount or 0
        entity = parsed.entity
        
        # A. Find the loan
        target_loan = get_loan_by_entity(user_id, entity)
        
        if not target_loan:
            return f"I couldn't find an active loan for **{entity}**."

        # B. Calculate new balance
        current_balance = target_loan['remaining_amount']
        new_balance = current_balance - repayment
        
        # C. Update Database & Return Signal
        if new_balance <= 0:
            close_memory_fact(target_loan['id'])
            add_memory_fact(user_id, "repayment", entity, repayment, f"Closed loan {target_loan['id']}")
            
            # SIGNAL: The word "settled" is what we will use later for notifications
            return f"Loan settled! {entity} paid off the full balance."
            
        else:
            update_remaining(target_loan['id'], new_balance)
            add_memory_fact(user_id, "repayment", entity, repayment, f"Partial payment")
            
            return (
                f"Recorded. {entity} paid **${repayment:.0f}**.\n"
                f"Remaining balance: **${new_balance:.0f}**."
            )

    # ... (Keep query_debts logic as is) ...


    # ==================================================
    # 3. QUERY DEBTS
    # ==================================================
    if parsed.intent == "query_debts":
        loans = get_active_loan_items(user_id)
        if not loans:
            return "You don’t have any active loans 🙂"
        return format_loans(loans)

    return "I wasn't sure how to process that."