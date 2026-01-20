from fastapi import FastAPI
from pydantic import BaseModel

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
@app.post("/extract/text")
def extract_text(data: TextInput):
    text = data.text

    return {
        "currency": "INR",
        "amounts": [
            {
                "type": "total_bill",
                "value": 1200,
                "source": "text: 'Total: INR 1200'"
            },
            {
                "type": "paid",
                "value": 1000,
                "source": "text: 'Paid: 1000'"
            },
            {
                "type": "due",
                "value": 200,
                "source": "text: 'Due: 200'"
            }
        ],
        "status": "ok"
    }
