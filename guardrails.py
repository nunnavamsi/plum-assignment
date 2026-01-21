# guardrails.py
def check_guardrails(text: str, numbers: list):
    """
    Guardrails to prevent unsafe or meaningless processing.
    """

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
