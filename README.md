#           AI-Powered Amount Detection in Medical Documents

## Overview
This project is a backend API built using FastAPI that extracts financial amounts
from medical bills or receipts provided as text input. The API identifies numeric
values, classifies them based on context (total, paid, due), and returns structured
JSON output.

---
## Live Demo

The backend is running locally and exposed using ngrok.

Base URL:
https://marielle-inviolable-javier.ngrok-free.dev

Swagger UI:
https://marielle-inviolable-javier.ngrok-free.dev/docs

Note: On first visit, ngrok may show a standard warning page.
Click "Visit Site" to continue.

---

## Tech Stack
- Python 3.11
- FastAPI
- Uvicorn
- OpenAI API
- Pydantic
- pytesseract & Pillow (OCR-ready)
---

## Features
- Text extraction
- Amount classification
- FastAPI backend

---

## Setup Instructions

### Prerequisites
- Python 3.11 installed
- pip package manager

### Steps to Run Locally

1. Install dependencies:
```bash
py -m pip install fastapi uvicorn
```

---

## Start the server:
```bash
py -m uvicorn main:app --reload
``` 

---

## Open browser and visit:
```text
http://127.0.0.1:8000/docs
``` 
---

## Architecture
The system follows a simple step-by-step processing pipeline:
```text
Input (Text / Image)
↓
Shared Guardrails Layer
↓
Numeric Extraction Module
↓
AI Reasoning (FILTER)
↓
AI Validation (APPROVE)
↓
Structured JSON Output
```
This modular pipeline makes the logic easy to extend and validate.

---

## API Usage Example
### Endpoint
POST /extract/text

### Example Request
```json
{
  "text": "Total INR 1200 Paid 1000 Due 200"
}
```

### Example Response
```json
{
  "currency": "INR",
  "amounts": [
    { "type": "total_bill", "value": 1200 },
    { "type": "paid", "value": 1000 },
    { "type": "due", "value": 200 }
  ],
  "status": "ok"
}
```
---

## Sample curl Request(curl & Postman)

You can test the API using the following curl command:
### curl – Text Extraction
```bash
curl -X POST http://127.0.0.1:8000/extract/text \
-H "Content-Type: application/json" \
-d '{"text":"Total INR 1200 Paid 1000 Due 200"}'
```
### Postman
Method: POST

URL: http://127.0.0.1:8000/extract/text

Headers: Content-Type: application/json

Body (raw / JSON):
```json
{
"text": "Total INR 1200 Paid 1000 Due 200"
}
```
Expected Response:
```json
{
"currency": "INR",
"raw_numbers": ["1200", "1000", "200"],
"status": "ok"
}
```
---




