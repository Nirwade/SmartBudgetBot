import json
from datetime import datetime

TRAINING_FILE = "training_data.jsonl"


def save_feedback(text, predicted, confirmed):
    record = {
        "timestamp": datetime.utcnow().isoformat(),
        "text": text,
        "predicted_intent": predicted,
        "confirmed_intent": confirmed
    }

    with open(TRAINING_FILE, "a") as f:
        f.write(json.dumps(record) + "\n")


def save_feedback(user_id, text, predicted, confirmed):
    record = {
        "timestamp": datetime.utcnow().isoformat(),
        "user_id": user_id,
        "text": text,
        "predicted_intent": predicted,
        "confirmed_intent": confirmed
    }

def save_feedback(user_id, text, predicted, confirmed, confidence, source):
    record = {
        "timestamp": datetime.utcnow().isoformat(),
        "user_id": user_id,
        "text": text,
        "predicted_intent": predicted,
        "confirmed_intent": confirmed,
        "confidence": confidence,
        "source": source
    }
