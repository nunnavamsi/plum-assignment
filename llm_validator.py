import json
from openai import OpenAI

# Initialize OpenAI client
client = OpenAI()


def filter_monetary_amounts(text: str, numbers: list):
    """
    FILTER stage (GFA):
    Use LLM reasoning to identify which numbers are monetary amounts.
    """
    prompt = f"""
    You are a medical billing analyst.

    Text:
    {text}

    Extracted Numbers:
    {numbers}

    Identify which numbers represent monetary amounts.
    Ignore dates, IDs, phone numbers.

    Return JSON only:
    {{
        "amounts": [
            {{ "value": "number", "reason": "short explanation" }}
        ]
    }}
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    return json.loads(response.choices[0].message.content)


def validate_amounts(amounts: list):
    """
    APPROVE stage (GFA):
    Validate extracted monetary amounts and assign confidence.
    """
    prompt = f"""
    Validate the following extracted monetary amounts from a medical bill.

    Amounts:
    {amounts}

    Check:
    - Internal consistency
    - Likelihood of being final payable amount

    Return JSON only:
    {{
        "approved": true/false,
        "confidence": 0-1,
        "explanation": "short explanation"
    }}
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    return json.loads(response.choices[0].message.content)
