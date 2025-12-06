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
# Store space name in Vercel client_key and value in env variables and HF variables and secrets
AMP_SPACE = os.getenv("AMP_SPACE")
client = Client(AMP_SPACE)

# --- Google Sheets logging constants ---
SHEET_URL = os.getenv("SHEET_URL")
SECRET_TOKEN = os.getenv("SECRET_TOKEN")

# 4. Request model
class SequenceRequest(BaseModel):
    sequence: str
    user: str = "anonymous"

# 5. Health check
@app.get("/")
def root():
    return {"message": "Proxy server running"}

# 6. Prediction endpoint
@app.post("/predict")
def predict(req: SequenceRequest):
    try:
        print("Received sequence:", repr(req.sequence))

        # --- HF prediction ---
        result = client.predict(
            sequence=req.sequence,
            api_name="/predict_peptide"
        )
        print("HF raw:", result)

        predictions = []

        if isinstance(result, dict) and "data" in result:
            for row in result["data"]:
                predictions.append({"target": row[0], "probability": float(row[1])})
        elif isinstance(result, list):
            for row in result:
                predictions.append({"target": row[0], "probability": float(row[1])})

        # ⭐ ADDED: Extract ONLY the probabilities for columns D–H
        hf_numbers = [p["probability"] for p in predictions]  # [0.1562, 0.3115, ...]
        print("hf_numbers:", hf_numbers)
        # ⭐ END ADDITION

        # --- POST to Google Sheet ---
        try:
            sheet_response = requests.post(
                url=SHEET_URL,
                headers={"Content-Type": "application/json"},
                json={
                    "sequence": req.sequence,
                    "user": req.user,
                    "source": "iOS app",
                    "token": SECRET_TOKEN,

                    # ⭐ ADDED: send numeric array only
                    "hf_numbers": hf_numbers
                    # ⭐ END ADDITION
                }
            )
            print("Sheet response:", sheet_response.text)
        except Exception as sheet_error:
            print("Failed to log to sheet:", sheet_error)

        return {
            "sequence": req.sequence,
            "predictions": predictions,
            "hf_numbers": hf_numbers  # optional
        }

    except Exception as e:
        print("Error:", e)
        return {
            "sequence": req.sequence,
            "predictions": [],
            "error": str(e)
        }
