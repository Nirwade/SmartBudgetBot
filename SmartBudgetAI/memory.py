# SmartBudgetAI/memory.py

from SmartBudgetAI.db import (
    add_memory_fact as db_add_memory_fact,
    get_memory_facts
)

def add_memory_fact(user_id, memory_type, entity, amount, description=None):
    db_add_memory_fact(
        user_id=user_id,
        memory_type=memory_type,
        entity=entity,
        amount=amount,
        description=description
    )

def get_active_loans(user_id):
    """
    Used by tests to verify state.
    Strictly filters for active debts (memory_type='loan').
    """
    facts = get_memory_facts(
        user_id=user_id,
        memory_type=None,
        active_only=True
    )
    # FIX: Filter out 'repayment' or other types
    return [f for f in facts if f['memory_type'] == 'loan']

def get_active_loan_items(user_id):
    """
    Used by chat_engine to list options for 'close loan'.
    """
    facts = get_memory_facts(user_id)
    
    # FIX: Ensure we only return items that are 'loan' AND 'active'
    return [
        f for f in facts
        if f.get("memory_type") == "loan"
        and f.get("status") == "active" 
        and f.get("remaining_amount", 0) > 0
    ]