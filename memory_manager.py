import re
import hashlib
import time

chat_history = {}
patient_state = {}

def hash_user_id(phone_number: str) -> str:
    """Returns a SHA-256 hash of the phone number to prevent PII exposure."""
    return hashlib.sha256(phone_number.encode('utf-8')).hexdigest()

def init_user_if_needed(hashed_id: str):
    if hashed_id not in chat_history:
        chat_history[hashed_id] = []
    if hashed_id not in patient_state:
        patient_state[hashed_id] = {
            "asked_age": False,
            "asked_gender": False,
            "active_treatment": None,
            "active_expert": None,
            "last_active": time.time()
        }

def update_patient_state(hashed_id: str, user_message: str, bot_response: str):
    init_user_if_needed(hashed_id)
    state = patient_state[hashed_id]
    state["last_active"] = time.time()

    # Simple keyword scanning logic
    user_msg_lower = user_message.lower()
    bot_msg_lower = bot_response.lower()

    history = chat_history.get(hashed_id, [])
    # Look at the bot message *before* the current one (skip the last one)
    prev_bot_msg = ""
    bot_msg_count = 0
    for msg in reversed(history):
        if msg["role"] == "model":
            bot_msg_count += 1
            if bot_msg_count == 2: # The previous one
                prev_bot_msg = msg["content"].lower()
                break

    # If bot asked about age in a previous interaction or this one, and user provided a number
    if "age" in bot_msg_lower or "വയസ്സ്" in bot_msg_lower or "വയസ്" in bot_msg_lower or "age" in prev_bot_msg or "വയസ്സ്" in prev_bot_msg or "വയസ്" in prev_bot_msg:
        # User replied with a number?
        if any(char.isdigit() for char in user_message):
            state["asked_age"] = True

    # Gender keywords (although strictly banned from asking directly, bot might infer or user might volunteer)
    gender_keywords = ["male", "female", "man", "woman", "boy", "girl", "പുരുഷൻ", "സ്ത്രീ", "ആൺ", "പെൺ"]
    if any(k in user_msg_lower for k in gender_keywords):
        state["asked_gender"] = True

def add_interaction(phone_number: str, user_message: str, bot_response: str):
    hashed_id = hash_user_id(phone_number)
    init_user_if_needed(hashed_id)
    history = chat_history[hashed_id]

    # Append interactions
    if user_message:
        history.append({"role": "user", "content": user_message})
    if bot_response:
        history.append({"role": "model", "content": bot_response})

    # Strictly limit to the last 8 messages (4 user, 4 bot) to cap memory
    if len(history) > 8:
        chat_history[hashed_id] = history[-8:]

    update_patient_state(hashed_id, user_message, bot_response)

def get_context(phone_number: str):
    hashed_id = hash_user_id(phone_number)
    init_user_if_needed(hashed_id)
    patient_state[hashed_id]["last_active"] = time.time()

    history = chat_history[hashed_id]
    state = patient_state[hashed_id]

    history_text = ""
    for msg in history:
        role = "User" if msg["role"] == "user" else "Ayur Care"
        history_text += f"{role}: {msg['content']}\n"

    # Build state note
    notes = []
    if state["asked_age"]:
        notes.append("age")
    if state["asked_gender"]:
        notes.append("gender")

    state_notes = ""
    if notes:
        known = " and ".join(notes)
        state_notes = f"\nSystem Note: You already know this patient's {known}. DO NOT ask for them again. Move straight to the symptom or treatment."

    return history_text, state_notes

async def clean_expired_sessions():
    """Garbage collects sessions older than 2 hours to prevent OOM errors."""
    current_time = time.time()
    expiry_limit = 7200 # 2 hours in seconds

    # Need to convert keys to list to avoid runtime error during dict modification
    expired_keys = [
        k for k, state in patient_state.items()
        if current_time - state.get("last_active", current_time) > expiry_limit
    ]

    for k in expired_keys:
        if k in chat_history:
            del chat_history[k]
        if k in patient_state:
            del patient_state[k]


def get_active_expert(phone_number: str):
    hashed_id = hash_user_id(phone_number)
    init_user_if_needed(hashed_id)
    return patient_state[hashed_id].get("active_expert")

def set_active_expert(phone_number: str, expert: str):
    hashed_id = hash_user_id(phone_number)
    init_user_if_needed(hashed_id)
    patient_state[hashed_id]["active_expert"] = expert
