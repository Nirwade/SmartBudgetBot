# SmartBudgetAI/intent_router.py

def detect_intent(text: str) -> str:
    """
    Lightweight intent classifier.
    Returns one of:
    - close_loan
    - create_loan
    - summary
    - reminder
    - unknown
    """
    text = text.lower()

    scores = {
        "close_loan": 0,
        "create_loan": 0,
        "summary": 0,
        "reminder": 0
    }

    CLOSE_WORDS = ["returned", "paid", "settled", "closed", "done"]
    CREATE_WORDS = ["lent", "gave", "loaned", "borrowed", "sent"]
    SUMMARY_WORDS = ["who owes", "how much", "total", "owed", "pending"]
    REMINDER_WORDS = ["due", "remind", "reminder"]

    for w in CLOSE_WORDS:
        if w in text:
            scores["close_loan"] += 1

    for w in CREATE_WORDS:
        if w in text:
            scores["create_loan"] += 1

    for w in SUMMARY_WORDS:
        if w in text:
            scores["summary"] += 1

    for w in REMINDER_WORDS:
        if w in text:
            scores["reminder"] += 1

    best_intent = max(scores, key=scores.get)
    return best_intent if scores[best_intent] > 0 else "unknown"
