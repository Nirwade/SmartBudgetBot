from dataclasses import dataclass
from typing import Optional
from SmartBudgetAI.intent_schema import ParsedIntent

@dataclass
class PendingConfirmation:
    user_id: str
    original_text: str
    parsed_intent: ParsedIntent
