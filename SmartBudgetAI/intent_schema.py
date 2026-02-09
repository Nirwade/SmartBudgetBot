from dataclasses import dataclass
from typing import Optional, List

@dataclass
class ParsedIntent:
    intent: str
    entity: Optional[str] = None
    amount: Optional[float] = None
    confidence: float = 0.0
    source: str = "rules"
    needs_confirmation: bool = False
    intent_candidates: Optional[List[str]] = None
