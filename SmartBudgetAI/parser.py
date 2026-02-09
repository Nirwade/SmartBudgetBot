# SmartBudgetAI/parser.py
import re
from SmartBudgetAI.intent_schema import ParsedIntent
from SmartBudgetAI.intent_specs import INTENT_SPECS

# Regex to catch "300", "300.50", "$300"
AMOUNT_REGEX = r"\b\d+(\.\d{1,2})?\b"

STOPWORDS = {
    "i", "me", "my", "you", "we", "us", "the", "a", "an", 
    "to", "from", "for", "with", "him", "her"
}

def extract_amount(text: str):
    m = re.search(AMOUNT_REGEX, text)
    return float(m.group()) if m else None

def extract_entity(text: str):
    # Split text and check for Title Case words that aren't stopwords
    # e.g. "John" -> Match. "him" -> Skip.
    words = text.split()
    for w in words:
        clean_w = w.strip(".,?!")
        if clean_w.istitle() and clean_w.lower() not in STOPWORDS:
            return clean_w
    return None

def parse_message(text: str) -> ParsedIntent:
    text_lower = text.lower()
    amount = extract_amount(text)
    entity = extract_entity(text)

    # 1. Check Explicit Keywords
    for intent, spec in INTENT_SPECS.items():
        for kw in spec["keywords"]:
            if kw in text_lower:
                return ParsedIntent(
                    intent=intent,
                    entity=entity,
                    amount=amount,
                    confidence=1.0
                )

    # 2. Ambiguous Case (No keywords, but Entity + Amount found)
    # e.g. "John 300"
    if entity and amount:
        return ParsedIntent(
            intent="clarify",
            entity=entity,
            amount=amount,
            confidence=0.5,
            needs_confirmation=True  # This triggers the CLARIFY state
        )

    # 3. Fallback
    return ParsedIntent(intent="clarify", confidence=0.0)