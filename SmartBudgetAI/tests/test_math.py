# SmartBudgetAI/tests/test_math.py
from SmartBudgetAI.chat_engine import handle_user_message
from SmartBudgetAI.memory import get_active_loans, add_memory_fact

def test_partial_repayment_math():
    # 1. Setup: User lends $100 to Mike
    add_memory_fact(1, "loan", "Mike", 100.0, "Test loan")
    
    # 2. Action: Mike pays $40
    # Note: We simulate the conversation flow
    reply = handle_user_message("Mike paid me 40", user_id=1)
    
    # 3. Verify Reply
    assert "Remaining balance" in reply
    assert "60" in reply
    
    # 4. Verify DB
    loans = get_active_loans(1)
    assert len(loans) == 1
    assert loans[0]['remaining_amount'] == 60.0

def test_full_repayment_closes_loan():
    # 1. Setup: User lends $50 to Mike
    add_memory_fact(1, "loan", "Mike", 50.0, "Test loan")
    
    # 2. Action: Mike pays $50
    reply = handle_user_message("Mike paid 50", user_id=1)
    
    # 3. Verify
    assert "settled" in reply.lower()
    
    # 4. DB should be empty of active loans
    loans = get_active_loans(1)
    assert len(loans) == 0