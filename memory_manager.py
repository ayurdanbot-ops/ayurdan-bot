import time

# In-memory storage
_sessions = {}
SESSION_TIMEOUT = 1800  # 30 minutes in seconds
MAX_HISTORY_LENGTH = 6

def get_session(user_id: str) -> dict:
    current_time = time.time()

    # Cleanup expired sessions
    expired_users = [
        uid for uid, session in _sessions.items()
        if current_time - session.get('last_accessed', 0) > SESSION_TIMEOUT
    ]
    for uid in expired_users:
        del _sessions[uid]

    if user_id not in _sessions:
        _sessions[user_id] = {
            'chat_history': [],
            'patient_state': {},
            'last_accessed': current_time
        }
    else:
        _sessions[user_id]['last_accessed'] = current_time

    return _sessions[user_id]

def add_message(user_id: str, message: dict):
    session = get_session(user_id)
    session['chat_history'].append(message)

    # Trim history
    if len(session['chat_history']) > MAX_HISTORY_LENGTH:
        session['chat_history'] = session['chat_history'][-MAX_HISTORY_LENGTH:]

def get_history(user_id: str) -> list:
    return get_session(user_id)['chat_history']
