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

# Replace with your exact HF Space name
client = Client("Ym420/peptide-function-classification")  

class SequenceRequest(BaseModel):
    sequence: str

@app.get("/")
def root():
    return {"message": "Peptide proxy server running"}

@app.post("/predict")
def predict(req: SequenceRequest):
    try:
        print("Received sequence:", repr(req.sequence))

        result = client.predict(
            sequence=req.sequence,
            api_name="/predict_peptide"
        )

        parsed = []
        for row in result:
            if isinstance(row, (list, tuple)) and len(row) == 2:
                parsed.append({
                    "target": str(row[0]),
                    "probability": float(row[1])
                })

        return {
            "sequence": req.sequence,
            "predictions": parsed
        }

    except Exception as e:
        return {
            "sequence": req.sequence,
            "predictions": [],
            "error": str(e)
        }
