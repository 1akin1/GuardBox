"""
GuardBox chatbot - inference module.

Importing this module is cheap and side-effect free: it loads the trained
model and intents, then exposes `get_response(message)`. It does NOT train
the model and does NOT start an interactive loop, so it is safe to import
from the desktop app or any other code.

  - To (re)train the model:        python train.py
  - To chat interactively:         python run_chatbot.py
"""
import json
import os
import random

import numpy as np
import torch

from nltk_utils import tokenize, bag_of_words
from model import NeuralNet

# Live database (used to answer status questions). If Firebase is not
# configured, status queries fail gracefully and fall back to a message.
try:
    from firebase_config import get_db
    db = get_db()
except Exception as e:  # pragma: no cover - config/network issues
    print(f"[chatbot] Firebase not available: {e}")
    db = None

_HERE = os.path.dirname(os.path.abspath(__file__))
_MODEL_PATH = os.path.join(_HERE, "chatbot_model.pth")
_INTENTS_PATH = os.path.join(_HERE, "intents.json")

# Load intents
with open(_INTENTS_PATH, "r", encoding="utf-8") as f:
    intents = json.load(f)

# Load trained model
_data = torch.load(_MODEL_PATH, map_location="cpu", weights_only=False)
input_size = _data["input_size"]
hidden_size = _data["hidden_size"]
output_size = _data["output_size"]
all_words = _data["all_words"]
tags = _data["tags"]

model = NeuralNet(input_size, hidden_size, output_size)
model.load_state_dict(_data["model_state"])
model.eval()

CONFIDENCE_THRESHOLD = 0.6


def _read(*path):
    """Safely read a value from the Firebase Realtime Database."""
    if db is None:
        return None
    ref = db
    for p in path:
        ref = ref.child(p)
    return ref.get().val()


def get_response(msg):
    """Classify a message and return a reply (live data where relevant)."""
    sentence = tokenize(msg)
    X = bag_of_words(sentence, all_words)
    X = torch.from_numpy(X).unsqueeze(0)

    output = model(X)
    _, predicted = torch.max(output, dim=1)
    tag = tags[predicted.item()]

    probs = torch.softmax(output, dim=1)
    confidence = probs[0][predicted.item()].item()

    if confidence <= CONFIDENCE_THRESHOLD:
        return "I'm not sure I understand. Can you try again?"

    # === Real-time sensor queries ===
    if tag == "check_weight":
        weight = _read("guardbox", "weight")
        return f"The current weight is {weight:.2f} grams." if weight is not None \
            else "I couldn't retrieve the weight right now."

    if tag == "box_status":
        locked = _read("guardbox", "locked")
        return "The box is currently locked." if locked else "The box is currently unlocked."

    if tag == "check_vibration":
        vibration = _read("guardbox", "vibration")
        return "Yes, vibration has been detected recently." if vibration \
            else "No vibration has been detected."

    if tag == "check_package":
        weight = _read("guardbox", "weight")
        if weight is not None and weight >= 100:
            return f"Yes, there is a package inside. The weight is approximately {weight:.0f} grams."
        return "No, the box appears to be empty."

    # === Aggregate stats queries ===
    if tag == "vibration_count":
        count = _read("guardbox_stats", "vibrations")
        return f"The box has recorded {count} vibration events." if count is not None \
            else "I couldn't retrieve the vibration count."

    if tag == "lock_count":
        count = _read("guardbox_stats", "locked")
        return f"The box has been locked {count} times." if count is not None \
            else "I couldn't retrieve the lock count."

    if tag == "delivery_count":
        count = _read("guardbox_stats", "deliveries")
        return f"There have been {count} package deliveries." if count is not None \
            else "I couldn't retrieve the delivery count."

    # === Fallback to a canned response from intents.json ===
    for intent in intents["intents"]:
        if tag == intent["tag"]:
            return random.choice(intent["responses"])

    return "I'm not sure I understand. Can you try again?"
