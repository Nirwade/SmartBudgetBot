import re
from datetime import datetime
from SmartBudgetAI.db import add_memory_fact

MONTHS = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4,
    "may": 5, "jun": 6, "jul": 7, "aug": 8,
    "sep": 9, "oct": 10, "nov": 11, "dec": 12
}

def parse_simple_date(text):
    match = re.search(r"(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s+(\d{1,2})", text)
    if match:
        month = MONTHS[match.group(1)]
        day = int(match.group(2))
        year = datetime.today().year
        return f"{year:04d}-{month:02d}-{day:02d}"
    return None

def extract_and_store_memory(text, user_id=1):
    text_lower = text.lower()

    loan_match = re.search(r"lent (\w+) \$?(\d+)", text_lower)
    if not loan_match:
        return None

    entity = loan_match.group(1).capitalize()
    amount = float(loan_match.group(2))

    event_date = parse_simple_date(text_lower)
    due_date = None

    if "return by" in text_lower:
        due_date = parse_simple_date(text_lower.split("return by")[-1])

    add_memory_fact(
        user_id=user_id,
        memory_type="loan",
        entity=entity,
        amount=amount,
        currency="USD",
        event_date=event_date,
        due_date=due_date,
        description=f"Lent money to {entity}"
    )

    return {
        "type": "loan",
        "entity": entity,
        "amount": amount,
        "event_date": event_date,
        "due_date": due_date
    }
