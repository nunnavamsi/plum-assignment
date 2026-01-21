import json
import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def _safe_json_parse(text: str):
    """
    Safely parse JSON from LLM output.
    Strips markdown, handles empty responses.
    """
    if not text:
        raise ValueError("LLM returned empty response")

    # Remove markdown code fences if present
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]

    return json.loads(text)


def filter_monetary_amounts(text: str, numbers: list):
    prompt = f"""
You are a medical billing analyst.

Text:
{text}

Extracted Numbers:
{numbers}

Identify which numbers represent monetary amounts.
Ignore dates, IDs, phone numbers.

Return STRICT JSON only (no text, no markdown):
{{
  "amounts": [
    {{ "value": 123, "reason": "short explanation" }}
  ]
}}
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    content = response.choices[0].message.content
    return _safe_json_parse(content)


def validate_amounts(amounts: list):
    prompt = f"""
Validate the following extracted monetary amounts from a medical bill.

Amounts:
{amounts}

Return STRICT JSON only (no text, no markdown):
{{
  "approved": true,
  "confidence": 0.85,
  "explanation": "short explanation"
}}
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    content = response.choices[0].message.content
    return _safe_json_parse(content)
