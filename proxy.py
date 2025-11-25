# Import FastAPI framework and supporting tools
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from gradio_client import Client
import requests
import os   # --- ADDED: for reading webhook URL from environment ---
import datetime  # --- ADDED: for timestamp logging ---


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

# --- ADDED: Google Sheets Apps Script webhook URL ---
GOOGLE_SHEETS_WEBHOOK = os.getenv("GOOGLE_SHEETS_WEBHOOK", "")
# Example value: "https://script.google.com/macros/s/XXXXXX/exec"


# 4. Request model
class SequenceRequest(BaseModel):
    sequence: str


# 5. Health check endpoint
@app.get("/")
def root():
    return {"message": "Proxy server running"}


# 6. Prediction endpoint
@app.post("/predict")
def predict(req: SequenceRequest):
    try:
        print("✅ Received sequence:", repr(req.sequence))

        # --- ADDED: Log timestamp + sequence to Google Sheet ---
        if GOOGLE_SHEETS_WEBHOOK:
            try:
                timestamp = datetime.datetime.utcnow().isoformat()

                # POST to the Apps Script webhook
                requests.post(
                    GOOGLE_SHEETS_WEBHOOK,
                    json={
                        "timestamp": timestamp,  # will appear in column A
                        "sequence": req.sequence  # will appear in column B
                    },
                    timeout=5
                )
                print("📄 Logged to Google Sheets:", timestamp, req.sequence)

            except Exception as sheet_err:
                print("⚠️ Google Sheet logging failed:", sheet_err)
        else:
            print("⚠️ GOOGLE_SHEETS_WEBHOOK not set; skipping sheet logging")


        # --- Call HF Space ---
        result = client.predict(
            sequence=req.sequence,
            api_name="/predict_peptide"   # MUST use slash for your HF Space
        )

        print("HF raw result:", result)

        # --- Convert HF result to JSON list ---
        predictions = []

        # Case 1: Gradio DataFrame-style dict
        if isinstance(result, dict) and "data" in result:
            for row in result["data"]:
                predictions.append({
                    "target": row[0],
                    "probability": float(row[1])
                })

        # Case 2: Simple list [["Gram+", 0.12], ...]
        elif isinstance(result, list):
            for row in result:
                predictions.append({
                    "target": row[0],
                    "probability": float(row[1])
                })

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

