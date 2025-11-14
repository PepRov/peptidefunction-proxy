from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from gradio_client import Client

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

client = Client("Ym420/peptide-function-classification")  # or add hf_token if private

class SequenceRequest(BaseModel):
    sequence: str

@app.get("/")
def root():
    return {"message": "Peptide proxy server running"}

@app.post("/predict")
def predict(req: SequenceRequest):
    try:
        result = client.predict(sequence=req.sequence, api_name="/predict_peptide")
        parsed = [{"target": row[0], "probability": float(row[1])} for row in result]
        return {"sequence": req.sequence, "predictions": parsed}
    except Exception as e:
        return {"sequence": req.sequence, "predictions": [], "error": str(e)}


# Vercel expects a callable named `handler`
from mangum import Mangum  # lightweight AWS Lambda/ASGI adapter
handler = Mangum(app)
