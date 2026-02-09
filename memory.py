from database import get_last_messages

def build_memory(session_id):
    history = get_last_messages(session_id)
    formatted = ""
    for role, msg in history:
        formatted += f"{role.upper()}: {msg}\n"
    return formatted
