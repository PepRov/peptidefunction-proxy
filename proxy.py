# Import FastAPI framework and supporting tools
from fastapi import FastAPI             # For creating the API app
from pydantic import BaseModel         # For parsing & validating request bodies
from fastapi.middleware.cors import CORSMiddleware  # To enable cross-origin requests
from gradio_client import Client       # To call Hugging Face Gradio API

# -----------------------------
# 1. Create FastAPI app
# -----------------------------
app = FastAPI(title="Peptide Function Proxy API")

# -----------------------------
# 2. Enable CORS
# -----------------------------
# This allows requests from any origin (important for iOS apps or web frontends)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)
return result
# -----------------------------
# 3. Initialize HF Space client
# -----------------------------
# Creating the client once at cold start avoids re-initializing per request
client = Client("Ym420/peptide-function-classification")  # Replace with your HF Space

# -----------------------------
# 4. Define request model
# -----------------------------
# FastAPI automatically parses JSON into this Pydantic model
class SequenceRequest(BaseModel):
    sequence: str   # The peptide sequence sent by the client

# -----------------------------
# 5. Health check endpoint
# -----------------------------
@app.get("/")
def root():
    """
    Simple endpoint to verify the proxy server is running.
    Returns a small JSON message.
    """
    return {"message": "Proxy server running"}

# -----------------------------
# 6. Prediction endpoint
# -----------------------------
@app.post("/predict")
def predict(req: SequenceRequest):
    """
    Receives a peptide sequence from the client, forwards it to the
    Hugging Face Space API, and returns the predictions in JSON.
    """
    try:
        # -----------------------------
        # 6a. Debug: print received sequence
        # -----------------------------
        print("✅ Received sequence:", repr(req.sequence))

        # -----------------------------
        # 6b. Call HF Space API
        # -----------------------------
        # This calls your Gradio API endpoint defined in app.py:
        #     gr.api(predict_peptide, api_name="predict_peptide")
        result = client.predict(
            sequence=req.sequence,
            api_name="predict_peptide"  # No leading slash needed
        )

        # -----------------------------
        # 6c. Debug: print raw HF result
        # -----------------------------
        print("✅ Raw result from HF:", result)

        # -----------------------------
        # 6d. Process HF Space output
        # -----------------------------
        # Expected format: 5 rows x 2 columns
        # Example: [["Gram+", 0.87], ["Fungus", 0.34], ...]
        predictions = []
        if isinstance(result, list):
            for row in result:
                if isinstance(row, (list, tuple)) and len(row) == 2:
                    # Convert each row to dictionary for JSON
                    predictions.append({
                        "target": str(row[0]),
                        "probability": float(row[1])
                    })

        # -----------------------------
        # 6e. Return JSON response
        # -----------------------------
        # FastAPI automatically converts this dict to JSON
        return {
            "sequence": req.sequence,
            "predictions": predictions
        }

    except Exception as e:
        # -----------------------------
        # 6f. Error handling
        # -----------------------------
        # Catch any exceptions and return a JSON error
        print("❌ Error in /predict:", str(e))
        return {
            "sequence": req.sequence,
            "predictions": [],
            "error": str(e)
        }
