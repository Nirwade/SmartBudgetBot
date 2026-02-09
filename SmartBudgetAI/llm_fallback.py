# SmartBudgetAI/llm_fallback.py
import json
import requests
import re
from SmartBudgetAI.intent_schema import ParsedIntent

# Ensure you have Ollama running with this model!
OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "llama3.2:3b"

SYSTEM_PROMPT = """
You are a financial intent parser.
Extract structured data from the user's message.

Output strictly valid JSON with these keys:
- "intent": One of ["loan_given", "loan_received", "query_debts", "clarify"]
- "entity": The person involved (capitalized Name) or null.
- "amount": The number found or null.

Example: "I bought lunch for John, $15"
JSON: {"intent": "loan_given", "entity": "John", "amount": 15}
"""

def clean_json_response(text):
    """Extract JSON object from potential markdown wrapping"""
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        return match.group(0)
    return text

def llm_fallback_parse(text: str) -> ParsedIntent:
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": text}
        ],
        "stream": False,
        "options": {"temperature": 0} # Deterministic output
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=30) # increase timeput for cpu interface
        response.raise_for_status()

        content = response.json()["message"]["content"]
        cleaned_content = clean_json_response(content)
        
        data = json.loads(cleaned_content)
        
        # Map raw intent to known schema if needed
        intent = data.get("intent", "clarify")
        
        # Return parsed intent with "LLM" source
        return ParsedIntent(
            intent=intent,
            entity=data.get("entity"),
            amount=data.get("amount"),
            confidence=0.65,  # Medium confidence (requires confirmation)
            source="llm",
            needs_confirmation=True # ALWAYS confirm LLM guesses
        )

    except Exception as e:
        # If LLM fails (offline/timeout), fallback to clarify
        return ParsedIntent(intent="clarify", confidence=0.0)