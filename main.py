from fastapi import FastAPI
from pydantic import BaseModel
from guardrails import check_guardrails

app = FastAPI(
    title="AI-Powered Amount Detection in Medical Documents",
    description="API to extract, normalize, and classify financial amounts from medical bills",
    version="1.0.0"
)
class TextInput(BaseModel):
    text: str

@app.get("/")
def home():
    return {"message": "Server is running"}

import re

def extract_numbers_from_text(text: str):
    return re.findall(r"\d+", text)

@app.post("/extract/text")
def extract_text(data: TextInput):
    try:
        text = data.text
        numbers = extract_numbers_from_text(text)

        guardrail_response = check_guardrails(text, numbers)
        if guardrail_response:
            return guardrail_response

        return {
            "currency": "INR",
            "raw_numbers": numbers,
            "status": "ok"
        }

    except Exception:
        return {
            "status": "no_amounts_found",
            "reason": "internal extraction error"
        }
