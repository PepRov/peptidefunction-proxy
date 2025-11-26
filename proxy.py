# Import FastAPI framework and supporting tools
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from gradio_client import Client
import requests
import time    # ⬅️ NEW: For timing retries


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

        # ----------------------------------------------------
        # NEW: Retry logic to prevent Vercel random timeouts
        # ----------------------------------------------------
        max_attempts = 3             # ⬅️ NEW: retry 3 times
        last_exception = None        # ⬅️ NEW: store error

        for attempt in range(1, max_attempts + 1):         # ⬅️ NEW
            try:
                print(f"🔄 HF request attempt {attempt}/{max_attempts}")   # ⬅️ NEW

                # --- Call HF Space ---
                # NEW: Increased timeout for slow HF Space
                result = client.predict(
                    sequence=req.sequence,
                    api_name="/predict_peptide",
                    timeout=30   # ⬅️ NEW: Force 30s timeout inside HF call
                )

                print("HF raw result:", result)
                break   # ⬅️ NEW: success → break retry loop

            except Exception as e:
                print(f"⚠️ HF attempt {attempt} failed:", e)   # ⬅️ NEW
                last_exception = e                             # ⬅️ NEW
                time.sleep(1.2)                                # ⬅️ NEW: small delay between retries

        # After retries, still failed → return error
        if last_exception and attempt == max_attempts:        # ⬅️ NEW
            raise last_exception                              # ⬅️ NEW


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
