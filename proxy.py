# Import FastAPI framework and supporting tools
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from gradio_client import Client
import requests

# 1. Create FastAPI app
app = FastAPI(title="Peptide Function Proxy API")

# 2. Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. Initialize HF Space client
client = Client("Ym420/peptide-function-classification")

# --- Google Sheets logging constants ---
SHEET_URL = "https://script.google.com/macros/s/AKfycbzRhAfsU1DFAiYM24bHWTNzfg2ZKbPNI31TfGfRDkB7u789aJgjvSYNlX9hYZaXDNHm/exec"  # Paste your Web App URL here
SECRET_TOKEN = "F8k9G2pQ1rXs7ZtL4bMv6YwA"  # Same token as in Apps Script

# 4. Request model
class SequenceRequest(BaseModel):
    sequence: str
    user: str = "anonymous"  # optional, default to anonymous

# 5. Health check endpoint
@app.get("/")
def root():
    return {"message": "Proxy server running"}

# 6. Prediction endpoint
@app.post("/predict")
def predict(req: SequenceRequest):
    try:
        print("✅ Received sequence:", repr(req.sequence))

        # --- Call HF Space ---
        result = client.predict(
            sequence=req.sequence,
            api_name="/predict_peptide"   # MUST use slash for your HF Space
        )
        print("HF raw result:", result)

        # --- Convert HF result to JSON list ---
        predictions = []

        # Case 1: Result is Gradio DataFrame dict
        if isinstance(result, dict) and "data" in result:
            for row in result["data"]:
                predictions.append({
                    "target": row[0],
                    "probability": float(row[1])
                })

        # Case 2: Result is simple list: [["Gram+", 0.12], ...]
        elif isinstance(result, list):
            for row in result:
                predictions.append({
                    "target": row[0],
                    "probability": float(row[1])
                })

        # ===========================
        # --- Log to Google Sheet ---
        # ===========================
        try:
            sheet_response = requests.post(
                url=SHEET_URL,
                headers={"Content-Type": "application/json"},
                json={
                    "sequence": req.sequence,
                    "user": getattr(req.user or "anonymous"),
                    "source": "iOS app",
                    "token": SECRET_TOKEN,  # ✅ Token included
                },
                timeout=5
            )
            sheet_result = sheet_response.text
            print("📌 Google Sheet response:", sheet_result)
        except Exception as sheet_error:
            print("⚠️ Failed to log to Google Sheet:", sheet_error)
        # ==========================================================

        return {
            "sequence": req.sequence,
            "predictions": predictions
        }

    except Exception as e:
        print("❌ Error in /predict:", e)
        return {
            "sequence": req.sequence,
            "predictions": [],
            "error": str(e)
        }


