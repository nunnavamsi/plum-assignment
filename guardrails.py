def check_guardrails(text: str, tokens: list):
    """
    Simple guardrail to stop processing noisy or empty documents.
    """
    if not text or not text.strip():
        return {
            "status": "no_amounts_found",
            "reason": "document too noisy"
        }

    if not tokens or len(tokens) == 0:
        return {
            "status": "no_amounts_found",
            "reason": "document too noisy"
        }

    return None
