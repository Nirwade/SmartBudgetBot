# SmartBudgetAI/rule_parser.py

import re
from SmartBudgetAI.intent_schema import ParsedIntent

AMOUNT_REGEX = r"\b\d+(\.\d{1,2})?\b"

STOPWORDS = {
    "i", "me", "my", "you", "we", "us",
    "the", "a", "an", "all", "was", "were",
    "to", "from", "for", "with", "him", "her"
}

LEND_WORDS = {"lend", "lent", "gave", "paid"}
RECEIVE_WORDS = {"received", "got", "repaid", "returned"}


def normalize_text(text: str) -> str:
    return " ".join(text.strip().split())


def extract_amount(text: str):
    match = re.search(AMOUNT_REGEX, text)
    return float(match.group()) if match else None


def extract_entity(text: str):
    for w in text.split():
        if w.istitle() and w.lower() not in STOPWORDS:
            return w
    return None


def rule_parse(text: str) -> ParsedIntent:
    normalized = normalize_text(text)
    text_lower = normalized.lower()

    amount = extract_amount(normalized)
    entity = extract_entity(normalized)

    # -------------------------------
    # Explicit loan given
    # -------------------------------
    if any(w in text_lower for w in LEND_WORDS):
        return ParsedIntent(
            intent="loan_given",
            entity=entity,
            amount=amount,
            confidence=0.9
        )

    # -------------------------------
    # Explicit loan received
    # -------------------------------
    if any(w in text_lower for w in RECEIVE_WORDS):
        return ParsedIntent(
            intent="loan_received",
            entity=entity,
            amount=amount,
            confidence=0.9
        )

    # -------------------------------
    # Ambiguous loan (entity + amount)
    # -------------------------------
    if entity and amount:
        return ParsedIntent(
            intent="clarify",
            entity=entity,
            amount=amount,
            confidence=0.5,
            intent_candidates=["loan_given", "loan_received"],
            needs_confirmation=True
        )

    # -------------------------------
    # Fallback
    # -------------------------------
    return ParsedIntent(
        intent="clarify",
        confidence=0.0
    )
