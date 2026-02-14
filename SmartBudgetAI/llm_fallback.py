import json
import requests
import os
from datetime import datetime
from SmartBudgetAI.intent_schema import ParsedIntent

OLLAMA_URL = "http://localhost:11434/api/chat"
# ✅ SWITCH BACK TO THE SMART MODEL
MODEL = "llama3.2:3b"
TRAINING_FILE = "training_data.jsonl"

def get_system_prompt():
    """Context for the financial parser."""
    now = datetime.now()
    return f"""
    You are a financial parser. Current Time: {now.strftime("%I:%M %p")}
    Extract JSON data.
    Keys: "intent" (loan_given/loan_received/query/clarify), "entity" (Name), "amount" (number).
    """

def get_few_shot_examples():
    """Reads training data to learn from past corrections."""
    if not os.path.exists(TRAINING_FILE): return ""
    examples = []
    try:
        with open(TRAINING_FILE, "r") as f:
            lines = f.readlines()
            for line in reversed(lines):
                if len(examples) >= 3: break # Limit to 3 to keep it FAST
                rec = json.loads(line)
                if rec.get("confirmed_intent") and rec["confirmed_intent"] != "rejected":
                    examples.append(f'User: "{rec["text"]}" -> {{"intent": "{rec["confirmed_intent"]}"}}')
    except: pass
    return "\nExamples:\n" + "\n".join(examples) if examples else ""

def chat_with_persona(text: str):
    """
    Party Mode: Handles chit-chat.
    """
    # Llama 3.2 is smart, so we can use a "System Prompt" again (it's cleaner)
    persona_system = f"""
    You are SmartBudget, a chill Gen Z financial assistant.
    Current Time: {datetime.now().strftime("%I:%M %p")}
    - Use lowercase mostly. Use emojis 💸💀.
    - Be brief (1 sentence).
    - If user says "hi", just say "yo what's good?".
    """

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": persona_system},
            {"role": "user", "content": text}
        ],
        "stream": False,
        "options": {"temperature": 0.8}
    }

    try:
        # ✅ WORKAROUND: Increased to 60s so it doesn't crash on slow CPUs
        response = requests.post(OLLAMA_URL, json=payload, timeout=60)
        response.raise_for_status()
        return response.json()["message"]["content"].strip()
    except Exception as e:
        print(f"Persona Error: {e}")
        return "my brain is buffering... 💀 (cpu timeout)"

def llm_fallback_parse(text: str) -> ParsedIntent:
    full_prompt = get_system_prompt() + get_few_shot_examples()

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": full_prompt},
            {"role": "user", "content": text}
        ],
        "stream": False,
        "options": {"temperature": 0} 
    }

    try:
        # ✅ WORKAROUND: Increased to 60s
        response = requests.post(OLLAMA_URL, json=payload, timeout=60)
        response.raise_for_status()

        content = response.json()["message"]["content"].strip()
        
        # Llama 3.2 is good at JSON, but we still clean it just in case
        if "{" in content:
            start = content.find("{")
            end = content.rfind("}") + 1
            content = content[start:end]

        data = json.loads(content)
        
        return ParsedIntent(
            intent=data.get("intent", "clarify"),
            entity=data.get("entity"),
            amount=data.get("amount"),
            confidence=0.75, 
            source="llm",
            needs_confirmation=True
        )

    except Exception:
        return ParsedIntent(intent="clarify", confidence=0.0)