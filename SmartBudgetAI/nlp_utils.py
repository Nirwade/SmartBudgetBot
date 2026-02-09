import re

def extract_amount(text):
    match = re.search(r'(\$|usd|rs|₹|€)?\s?(\d+(?:\.\d+)?)', text.lower())
    if match:
        return float(match.group(2))
    return None

def extract_entity(text):
    # Simple heuristic: first capitalized word
    words = text.split()
    for w in words:
        if w.istitle():
            return w
    return None