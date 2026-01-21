# AI-Powered Amount Detection in Medical Documents

## Overview
This project is a backend API built using **FastAPI** that extracts financial amounts from medical bills or receipts.  
The system handles OCR noise, normalizes numeric values, classifies amounts by context (total, paid, due), and returns **structured, auditable JSON output**.

The API is designed to expose **each processing step independently** for evaluation clarity while maintaining a clean end-to-end pipeline.

---

## Live Demo
The backend is running locally and exposed using **ngrok**.

**Base URL:**  
https://marielle-inviolable-javier.ngrok-free.dev  

**Swagger UI:**  
https://marielle-inviolable-javier.ngrok-free.dev/docs  

> Note: On first visit, ngrok may show a standard warning page. Click **"Visit Site"** to continue.

---

## Tech Stack
- Python 3.11
- FastAPI
- Uvicorn
- OpenAI API
- Pydantic  
- Regex-based OCR normalization  
- OCR-ready (pytesseract & Pillow compatible)

---

## Features
- OCR-aware numeric extraction
- Robust OCR error normalization
- Context-based amount classification (Total / Paid / Due)
- AI-assisted amount validation
- Guardrails for noisy or invalid documents
- Step-by-step API design for evaluation
- Interactive Swagger UI

---

## Architecture
The system follows a **clear, modular pipeline**:

```text
Input (Text / OCR Output)
        ↓
Guardrails Layer
        ↓
Raw Token Extraction 
        ↓
Numeric Normalization 
        ↓
Context Classification 
        ↓
Final Output with Provenance 

```
Each step is independently testable through a dedicated API endpoint.

---

## API Endpoints 
| Step | Endpoint | Description |
|------|----------|-------------|
| Step 1 | POST `/extract/text` | OCR + raw numeric token extraction |
| Step 2 | POST `/extract/normalized` | OCR correction & numeric normalization |
| Step 3 | POST `/extract/classified` | Context-based classification |
| Step 4 | POST `/extract/final` | Final structured output with provenance |



### Step 1 – OCR / Text Extraction
####  Endpoint:
POST /extract/text

#### Request
```json
{
  "text": "T0tal: Rs l200 | Pald: 1000 | Due: 200 | Discount: 10%"
}
```

#### Response
```json
{
  "raw_tokens": ["1200", "1000", "200", "10%"],
  "currency_hint": "INR",
  "confidence": 0.74
}
```

### Step 2 – Normalization

#### Endpoint:
POST /extract/normalized

#### Response
```json
{
  "normalized_amounts": [1200, 1000, 200],
  "normalization_confidence": 0.82
}
```

### Step 3 – Classification by Context

#### Endpoint:
POST /extract/classified

#### Response
```json
{
  "amounts": [
    {"type": "total_bill", "value": 1200},
    {"type": "paid", "value": 1000},
    {"type": "due", "value": 200}
  ],
  "confidence": 0.80
}
```

### Step 4 – Final Output with Provenance

#### Endpoint:
POST /extract/final

#### Response
```json
{
  "currency": "INR",
  "amounts": [
    {"type": "total_bill", "value": 1200, "source": "text: 'Total: INR 1200'"},
    {"type": "paid", "value": 1000, "source": "text: 'Paid: 1000'"},
    {"type": "due", "value": 200, "source": "text: 'Due: 200'"}
  ],
  "status": "ok"
}
```
---

## Guardrails
If the document is empty or too noisy:
```json
{
  "status": "no_amounts_found",
  "reason": "document too noisy"
}
```
---

## Setup Instructions

### Prerequisites

- Python 3.11
- pip package manager

### Run Locally

Install dependencies:
```bash
pip install fastapi uvicorn
```
Start the server:
```bash
uvicorn main:app --reload
```
Open Swagger UI:
```text
http://127.0.0.1:8000/docs
```
---

## Sample cURL Request
```text
curl -X POST http://127.0.0.1:8000/extract/text \
-H "Content-Type: application/json" \
-d '{"text":"Total INR 1200 Paid 1000 Due 200"}'
```
---

## Design Notes

- Each processing step is exposed as a separate endpoint for evaluation clarity.

- Steps 3 and 4 share internal logic but return different outputs as required by the problem statement.

- The system is extensible to OCR image inputs with minimal changes.

--- 

## Conclusion
This project demonstrates:

- OCR-aware data extraction

- Robust numeric normalization

- Context-based classification

- Clean, auditable API design

- Practical backend engineering for real-world documents

---
