# Import FastAPI framework and supporting tools
from fastapi import FastAPI, Request  # ✅ Added Request to detect web/iOS source
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
SHEET_URL = "https://script.google.com/macros/s/AKfycbzRhAfsU1DFAiYM24bHWTNzfg2ZKbPNI31TfGfRDkB7u789aJgjvSYNlX9hYZaXDNHm/exec"
SECRET_TOKEN = "F8k9G2pQ1rXs7ZtL4bMv6YwA"

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
async def predict(req: SequenceRequest = None, request: Request = None):
    try:
        # -----------------------------
        # Determine sequence and user
        # -----------------------------
        data = {}
        if req:  # iOS / app JSON request
            data["sequence"] = req.sequence
            data["user"] = req.user or "anonymous"
        else:  # Web or other JSON
            body = await request.json()
            data["sequence"] = body.get("sequence", "")
            data["user"] = body.get("user", "anonymous")

        print("✅ Received sequence:", repr(data["sequence"]))

        # --- Call HF Space ---
        result = client.predict(
            sequence=data["sequence"],
            api_name="/predict_peptide"   # MUST use slash for your HF Space
        )
        print("HF raw result:", result)

        # --- Convert HF result to JSON list ---
        predictions = []

        # Case 1: Result is Gradio DataFrame dict
        if isinstance(result, dict) and "data" in result:
            for row in result["data"]:
                predictions.append({"target": row[0], "probability": float(row[1])})

        # Case 2: Result is simple list: [["Gram+", 0.12], ...]
        elif isinstance(result, list):
            for row in result:
                predictions.append({"target": row[0], "probability": float(row[1])})

        # ===========================
        # --- Log to Google Sheet ---
        # ===========================
        try:
            user_agent = request.headers.get("user-agent", "").lower()
            source = "web" if "mozilla" in user_agent or "chrome" in user_agent else "iOS app"

            sheet_response = requests.post(
                url=SHEET_URL,
                headers={"Content-Type": "application/json"},
                json={
                    "sequence": data["sequence"],
                    "user": data["user"],
                    "source": source,
                    "token": SECRET_TOKEN,
                },
                timeout=5
            )
            print("📌 Google Sheet response:", sheet_response.text)
        except Exception as sheet_error:
            print("⚠️ Failed to log to Google Sheet:", sheet_error)
        # ==========================================================

        return {"sequence": data["sequence"], "predictions": predictions}

    except Exception as e:
        print("❌ Error in /predict:", e)
        return {"sequence": "", "predictions": [], "error": str(e)}



