# Import FastAPI framework and supporting tools
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from gradio_client import Client
import requests
import os

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
SHEET_URL = os.getenv("SHEET_URL")
SECRET_TOKEN = os.getenv("SECRET_TOKEN")

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

        # ⭐ ADDED: Convert predictions to HF-style array-of-arrays
        # This is REQUIRED by your Google Apps Script (columns D–M)
        hf_data = [[p["target"], p["probability"]] for p in predictions]
        print("hf_data to send to Sheet:", hf_data)
        # ⭐ END ADDITION


        # ===========================
        # --- Log to Google Sheet ---
        # ===========================
        try:
            sheet_response = requests.post(
                url=SHEET_URL,
                headers={"Content-Type": "application/json"},
                json={
                    "sequence": req.sequence,
                    "user": req.user or "anonymous",
                    "source": "iOS app",
                    "token": SECRET_TOKEN,

                    # ⭐ ADDED: send predictions to Apps Script
                    # This corresponds to Column 4–13 in your Sheet
                    "hf_data": hf_data
                    # ⭐ END ADDITION
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
            "predictions": predictions,  # unchanged, same return to your iOS app
        }

    except Exception as e:
        print("❌ Error in /predict:", e)
        return {
            "sequence": req.sequence,
            "predictions": [],
            "error": str(e)
        }
