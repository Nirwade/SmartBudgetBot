from SmartBudgetAI.chat_engine import handle_user_message

def test_ambiguous_loan_triggers_clarification():
    reply = handle_user_message("John 300", user_id=1)

    assert "lend" in reply.lower()
    assert "repay" in reply.lower()
