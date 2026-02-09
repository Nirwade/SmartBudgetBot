from SmartBudgetAI.chat_engine import handle_user_message
from SmartBudgetAI.memory import add_memory_fact, get_active_loans

def test_partial_repayment_math():
    # 1. Setup: User lends $100 to Mike
    add_memory_fact(1, "loan", "Mike", 100.0, "Test loan")
    
    # 2. Action: "Mike repaid 40"
    # This triggers the "Soft Confirmation" question
    reply1 = handle_user_message("Mike repaid 40", user_id=1)
    assert "Do you want to record" in reply1
    
    # 3. Confirm with "Yes"
    reply2 = handle_user_message("yes", user_id=1)
    
    # 4. Verify Reply has the math
    assert "Remaining balance" in reply2
    assert "60" in reply2
    
    # 5. Verify DB updated
    # Now this will correctly return 1 (The loan) and ignore the Repayment record
    loans = get_active_loans(1)
    assert len(loans) == 1
    assert loans[0]['remaining_amount'] == 60.0

def test_full_repayment_closes_loan():
    # 1. Setup: User lends $50 to Mike
    add_memory_fact(1, "loan", "Mike", 50.0, "Test loan")
    
    # 2. Action: "Mike repaid 50"
    handle_user_message("Mike repaid 50", user_id=1)
    
    # 3. Confirm
    reply2 = handle_user_message("yes", user_id=1)
    
    # 4. Verify Signal
    assert "settled" in reply2.lower()
    
    # 5. DB should be empty of ACTIVE LOANS (Repayment record exists but is ignored)
    loans = get_active_loans(1)
    assert len(loans) == 0