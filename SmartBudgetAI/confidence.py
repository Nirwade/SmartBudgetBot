from SmartBudgetAI.intent_specs import INTENT_SPECS

CONF_EXECUTE = 0.75
CONF_LLM = 0.45


def compute_confidence(parsed):
    """
    Confidence is based on:
    1. Intent detected
    2. Required fields satisfied
    """

    score = 0.0

    # Intent detected
    if parsed.intent in INTENT_SPECS:
        score += 0.4
    else:
        return 0.0  # unknown / clarify stays low

    spec = INTENT_SPECS[parsed.intent]
    required = spec.get("required", [])

    # Check required fields
    missing = []

    for field in required:
        if getattr(parsed, field) is None:
            missing.append(field)

    # Field-based confidence
    if not missing:
        score += 0.6
    else:
        # Partial credit for partial info
        filled = len(required) - len(missing)
        if required:
            score += 0.6 * (filled / len(required))

    return round(score, 2)
