from SmartBudgetAI.chat_engine import handle_user_message
from SmartBudgetAI.memory import add_memory_fact, get_active_loans

def test_close_loan_multiple_options():
    user_id = 3

    add_memory_fact(user_id, "loan", "John", 100, "test")
    add_memory_fact(user_id, "loan", "Alex", 200, "test")

    reply = handle_user_message("close loan", user_id)

    assert "multiple" in reply.lower()
    assert "john" in reply.lower()
    assert "alex" in reply.lower()

    reply = handle_user_message("first", user_id)
    assert "closed" in reply.lower()

    loans = get_active_loans(user_id)
    assert len(loans) == 1
