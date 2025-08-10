def detect_intent(text: str) -> str:
    t = (text or "").lower()
    if any(k in t for k in ["where", "direction", "locate", "how to get"]):
        return "ask_directions"
    if any(k in t for k in ["open", "hour", "time"]):
        return "clinic_hours"
    if any(k in t for k in ["check my appointment", "my appointment", "appointment status", "check appointment"]):
        return "check_appointment"
    return "fallback"
