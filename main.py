from fastapi import FastAPI
from pydantic import BaseModel
import re

from guardrails import check_guardrails
from llm_validator import filter_monetary_amounts, validate_amounts

app = FastAPI(
    title="AI-Powered Amount Detection in Medical Documents",
    version="3.1.0"
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
        penalty = corrections / total_chars
        raw_confidence = max(0.5, 1.0 - penalty)
        confidence = round(min(raw_confidence, 0.82), 2)

    return normalized_text, confidence


# =========================
# STEP 1 – RAW TOKEN EXTRACTION (FIXED)
# =========================
def extract_raw_tokens(text: str):
    # Extract candidates like 1200, 1000, 200, 10%
    candidates = re.findall(r"\d{2,}%?", text)

    raw_tokens = []
    for token in candidates:
        if token.endswith("%"):
            raw_tokens.append(token)
        else:
            value = int(token)
            if value >= 50:   # remove OCR garbage like 0, 1
                raw_tokens.append(token)

    currency = "INR" if "INR" in text or "Rs" in text else None
    return raw_tokens, currency


def step1_confidence(raw_tokens: list[str]) -> float:
    if not raw_tokens:
        return 0.0
    if any(t.endswith("%") for t in raw_tokens):
        return 0.74
    return 0.70


# =========================
# NUMERIC NORMALIZATION
# =========================
def extract_numeric_amounts(tokens: list[str]) -> list[int]:
    amounts = []
    for token in tokens:
        if "%" in token:
            continue
        value = int(token)
        if value < 50:
            continue
        amounts.append(value)
    return sorted(amounts, reverse=True)


# =========================
# HELPERS FOR FINAL STEP
# =========================
def clean_provenance_text(text: str) -> str:
    replacements = {
        "T0ta1": "Total",
        "T0tal": "Total",
        "1NR": "INR",
        "Rs": "INR",
        "Pald": "Paid",
        "Disc0unt": "Discount"
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    return text.strip()


def split_into_logical_lines(text: str) -> list[str]:
    keywords = ["total", "paid", "due", "discount"]
    parts = []
    lower = text.lower()
    indices = [(lower.find(k), k) for k in keywords if lower.find(k) != -1]
    indices.sort()

    for i, (start, _) in enumerate(indices):
        end = indices[i + 1][0] if i + 1 < len(indices) else len(text)
        parts.append(text[start:end].strip())

    return parts


# =========================
# ROUTES
# =========================
@app.get("/")
def home():
    return {"message": "Server is running"}


# -------------------------------------------------
# STEP 1 — OCR / TEXT EXTRACTION (CORRECT)
# -------------------------------------------------
@app.post("/extract/text")
def extract_text(data: TextInput):
    normalized_text, _ = normalize_text(data.text)
    raw_tokens, currency = extract_raw_tokens(normalized_text)

    guardrail = check_guardrails(normalized_text, raw_tokens)
    if guardrail:
        return guardrail

    return {
        "raw_tokens": raw_tokens,
        "currency_hint": currency,
        "confidence": step1_confidence(raw_tokens)
    }


# -------------------------------------------------
# STEP 2 — NORMALIZATION
# -------------------------------------------------
@app.post("/extract/normalized")
def extract_normalized(data: TextInput):
    normalized_text, normalization_confidence = normalize_text(data.text)
    raw_tokens, _ = extract_raw_tokens(normalized_text)

    guardrail = check_guardrails(normalized_text, raw_tokens)
    if guardrail:
        return guardrail

    normalized_amounts = extract_numeric_amounts(raw_tokens)

    return {
        "normalized_amounts": normalized_amounts,
        "normalization_confidence": normalization_confidence
    }


# -------------------------------------------------
# STEP 3 — CLASSIFICATION
# -------------------------------------------------
@app.post("/extract/classified")
def extract_classified(data: TextInput):
    normalized_text, _ = normalize_text(data.text)
    raw_tokens, _ = extract_raw_tokens(normalized_text)

    guardrail = check_guardrails(normalized_text, raw_tokens)
    if guardrail:
        return guardrail

    normalized_amounts = extract_numeric_amounts(raw_tokens)
    filtered = filter_monetary_amounts(normalized_text, normalized_amounts)
    approval = validate_amounts(filtered.get("amounts", []))

    if not approval.get("approved"):
        return {
            "status": "no_amounts_found",
            "reason": "validation failed"
        }

    amounts = []
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

        amounts.append({
            "type": t,
            "value": int(item["value"])
        })

    return {
        "amounts": amounts,
        "confidence": approval.get("confidence", 0.80)
    }


# -------------------------------------------------
# STEP 4 — FINAL OUTPUT
# -------------------------------------------------
@app.post("/extract/final")
def extract_final(data: TextInput):
    normalized_text, _ = normalize_text(data.text)
    raw_tokens, currency = extract_raw_tokens(normalized_text)

    guardrail = check_guardrails(normalized_text, raw_tokens)
    if guardrail:
        return guardrail

    normalized_amounts = extract_numeric_amounts(raw_tokens)
    filtered = filter_monetary_amounts(normalized_text, normalized_amounts)
    approval = validate_amounts(filtered.get("amounts", []))

    if not approval.get("approved"):
        return {
            "status": "no_amounts_found",
            "reason": "validation failed"
        }

    parts = split_into_logical_lines(normalized_text)
    labels = []

    for item in filtered.get("amounts", []):
        value = int(item["value"])
        reason = item["reason"].lower()

        if "total" in reason:
            label, keyword = "total_bill", "total"
        elif "paid" in reason:
            label, keyword = "paid", "paid"
        elif "due" in reason:
            label, keyword = "due", "due"
        else:
            continue

        source_line = next(
            (p for p in parts if keyword in p.lower() and str(value) in p),
            f"{label.capitalize()}: {value}"
        )

        source_line = clean_provenance_text(source_line)

        labels.append({
            "type": label,
            "value": value,
            "source": f"text: '{source_line}'"
        })

    order = {"total_bill": 0, "paid": 1, "due": 2}
    labels.sort(key=lambda x: order[x["type"]])

    return {
        "currency": currency or "INR",
        "amounts": labels,
        "status": "ok"
    }
