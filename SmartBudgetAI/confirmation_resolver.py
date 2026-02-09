from SmartBudgetAI.intent_schema import ParsedIntent


def resolve_confirmation(user_reply: str, pending: ParsedIntent) -> ParsedIntent:
    reply = user_reply.lower()

    if "lend" in reply or "gave" in reply:
        return ParsedIntent(
            intent="loan_given",
            entity=pending.entity,
            amount=pending.amount,
            confidence=0.9
        )

    if "paid" in reply or "returned" in reply or "repaid" in reply:
        return ParsedIntent(
            intent="loan_received",
            entity=pending.entity,
            amount=pending.amount,
            confidence=0.9
        )

    return ParsedIntent(
        intent="clarify",
        confidence=0.4
    )
