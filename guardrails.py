def check_guardrails(text, numbers):
    if not text or text.strip() == "":
        return {
            "status": "no_amounts_found",
            "reason": "empty or invalid document"
        }

    if not numbers:
        return {
            "status": "no_amounts_found",
            "reason": "document too noisy"
        }

    return None
