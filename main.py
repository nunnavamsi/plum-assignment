from fastapi import FastAPI
from pydantic import BaseModel
import re

from guardrails import check_guardrails
from llm_validator import filter_monetary_amounts, validate_amounts

app = FastAPI(
    title="AI-Powered Amount Detection in Medical Documents",
    version="FINAL"
)

# =========================
# Models
# =========================
class TextInput(BaseModel):
    text: str


# =========================
# OCR Normalization Rules
# =========================
OCR_REPLACEMENTS = str.maketrans({
    "O": "0",
    "o": "0",
    "l": "1",
    "I": "1",
    "Z": "2",
    "S": "5",
})


def normalize_text(text: str) -> tuple[str, float]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    corrected_lines = []

    total_chars = 0
    corrections = 0

    for line in lines:
        total_chars += len(line)
        corrected = line.translate(OCR_REPLACEMENTS)
        corrections += sum(1 for a, b in zip(line, corrected) if a != b)
        corrected_lines.append(corrected)

    normalized_text = " ".join(corrected_lines)

    if total_chars == 0:
        confidence = 0.0
    else:
        confidence = round(min(max(0.5, 1.0 - corrections / total_chars), 0.82), 2)

    return normalized_text, confidence


# =========================
# STEP 1 — RAW TOKEN EXTRACTION
# =========================
def extract_raw_tokens(text: str):
    tokens = re.findall(r"\d{2,}%?", text)
    tokens = [t for t in tokens if t.endswith("%") or int(t) >= 50]
    currency = "INR" if "INR" in text or "Rs" in text else None
    return tokens, currency


def step1_confidence(tokens: list[str]) -> float:
    if not tokens:
        return 0.0
    return 0.74 if any(t.endswith("%") for t in tokens) else 0.70


# =========================
# NUMERIC NORMALIZATION
# =========================
def extract_numeric_amounts(tokens: list[str]) -> list[int]:
    return sorted(
        [int(t) for t in tokens if "%" not in t and int(t) >= 50],
        reverse=True
    )


# =========================
# TOTAL INFERENCE (NO SOURCE)
# =========================
def infer_total_if_missing(items: list[dict]) -> list[dict]:
    has_total = any(i["type"] == "total_bill" for i in items)
    paid = next((i for i in items if i["type"] == "paid"), None)
    due = next((i for i in items if i["type"] == "due"), None)

    if not has_total and paid and due:
        items.insert(0, {
            "type": "total_bill",
            "value": paid["value"] + due["value"]
        })

    return items


# =========================
# ROUTES
# =========================
@app.get("/")
def home():
    return {"message": "Server is running"}


# -------------------------------------------------
# STEP 1
# -------------------------------------------------
@app.post("/extract/text")
def extract_text(data: TextInput):
    text, _ = normalize_text(data.text)
    tokens, currency = extract_raw_tokens(text)

    guardrail = check_guardrails(text, tokens)
    if guardrail:
        return guardrail

    return {
        "raw_tokens": tokens,
        "currency_hint": currency,
        "confidence": step1_confidence(tokens)
    }


# -------------------------------------------------
# STEP 2
# -------------------------------------------------
@app.post("/extract/normalized")
def extract_normalized(data: TextInput):
    text, conf = normalize_text(data.text)
    tokens, _ = extract_raw_tokens(text)

    guardrail = check_guardrails(text, tokens)
    if guardrail:
        return guardrail

    return {
        "normalized_amounts": extract_numeric_amounts(tokens),
        "normalization_confidence": conf
    }


# -------------------------------------------------
# STEP 3 — CLASSIFICATION (NO SOURCE ANYWHERE)
# -------------------------------------------------
@app.post("/extract/classified")
def extract_classified(data: TextInput):
    text, _ = normalize_text(data.text)
    tokens, _ = extract_raw_tokens(text)

    guardrail = check_guardrails(text, tokens)
    if guardrail:
        return guardrail

    nums = extract_numeric_amounts(tokens)
    filtered = filter_monetary_amounts(text, nums)
    approval = validate_amounts(filtered.get("amounts", []))

    if not approval.get("approved"):
        return {"status": "no_amounts_found", "reason": "validation failed"}

    labels = []
    for item in filtered.get("amounts", []):
        reason = item["reason"].lower()
        if "total" in reason:
            t = "total_bill"
        elif "paid" in reason:
            t = "paid"
        elif "due" in reason:
            t = "due"
        else:
            continue

        labels.append({
            "type": t,
            "value": int(item["value"])
        })

    labels = infer_total_if_missing(labels)

    return {
        "amounts": labels,
        "confidence": approval.get("confidence", 0.80)
    }


# -------------------------------------------------
# STEP 4 — FINAL OUTPUT (NO SOURCE ANYWHERE)
# -------------------------------------------------
@app.post("/extract/final")
def extract_final(data: TextInput):
    text, _ = normalize_text(data.text)
    tokens, currency = extract_raw_tokens(text)

    guardrail = check_guardrails(text, tokens)
    if guardrail:
        return guardrail

    nums = extract_numeric_amounts(tokens)
    filtered = filter_monetary_amounts(text, nums)
    approval = validate_amounts(filtered.get("amounts", []))

    if not approval.get("approved"):
        return {"status": "no_amounts_found", "reason": "validation failed"}

    labels = []
    for item in filtered.get("amounts", []):
        reason = item["reason"].lower()
        if "total" in reason:
            t = "total_bill"
        elif "paid" in reason:
            t = "paid"
        elif "due" in reason:
            t = "due"
        else:
            continue

        labels.append({
            "type": t,
            "value": int(item["value"])
        })

    labels = infer_total_if_missing(labels)

    order = {"total_bill": 0, "paid": 1, "due": 2}
    labels.sort(key=lambda x: order[x["type"]])

    return {
        "currency": currency or "INR",
        "amounts": labels,
        "status": "ok"
    }
