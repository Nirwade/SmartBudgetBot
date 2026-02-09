from SmartBudgetAI.chat_engine import handle_user_message
from SmartBudgetAI.memory import get_active_loans

def test_confirmation_yes_executes():
    handle_user_message("John 300", user_id=1)
    reply = handle_user_message("I lent him", user_id=1)

    assert "lend" in reply.lower()

    reply = handle_user_message("yes", user_id=1)

    assert "recorded" in reply.lower()
    loans = get_active_loans(1)
    assert len(loans) == 1
    assert loans[0]["entity"] == "John"


def test_confirmation_no_aborts():
    handle_user_message("John 300", user_id=2)
    handle_user_message("I lent him", user_id=2)

    reply = handle_user_message("no", user_id=2)

    assert "rephrase" in reply.lower()
