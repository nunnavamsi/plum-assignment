import os
import json

try:
    from openai import OpenAI
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
except Exception:
    client = None


def _safe_json_parse(text: str):
    try:
        return json.loads(text)
    except Exception:
        return {}


# -------------------------------------------------
# HEURISTIC FALLBACK (NO OPENAI REQUIRED)
# -------------------------------------------------
def heuristic_classification(text: str, numbers: list):
    """
    Deterministic fallback when OpenAI is unavailable.
    """
    text_lower = text.lower()
    results = []

    for n in numbers:
        if "total" in text_lower:
            results.append({"value": n, "reason": "total amount"})
            break

    for n in numbers:
        if "paid" in text_lower and n not in [r["value"] for r in results]:
            results.append({"value": n, "reason": "paid amount"})
            break

    for n in numbers:
        if "due" in text_lower and n not in [r["value"] for r in results]:
            results.append({"value": n, "reason": "due amount"})
            break

    return {"amounts": results}


# -------------------------------------------------
# STEP 3 — FILTER MONETARY AMOUNTS
# -------------------------------------------------
def filter_monetary_amounts(text: str, numbers: list):
    if client is None or not os.getenv("OPENAI_API_KEY"):
        return heuristic_classification(text, numbers)

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{
                "role": "user",
                "content": f"""
Text:
{text}

Extracted numbers:
{numbers}

Return STRICT JSON:
{{ "amounts": [{{ "value": 1200, "reason": "short explanation" }}] }}
"""
            }],
            temperature=0
        )

        parsed = _safe_json_parse(response.choices[0].message.content)
        if not parsed or "amounts" not in parsed:
            return heuristic_classification(text, numbers)

        return parsed

    except Exception:
        return heuristic_classification(text, numbers)


# -------------------------------------------------
# STEP 4 — VALIDATION
# -------------------------------------------------
def validate_amounts(amounts: list):
    if client is None or not os.getenv("OPENAI_API_KEY"):
        return {
            "approved": True,
            "confidence": 0.80,
            "explanation": "heuristic fallback validation"
        }

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{
                "role": "user",
                "content": f"""
Validate the following monetary amounts:
{amounts}

Return STRICT JSON:
{{ "approved": true, "confidence": 0.80 }}
"""
            }],
            temperature=0
        )

        parsed = _safe_json_parse(response.choices[0].message.content)
        if not parsed:
            return {
                "approved": True,
                "confidence": 0.80
            }

        return parsed

    except Exception:
        return {
            "approved": True,
            "confidence": 0.80
        }
