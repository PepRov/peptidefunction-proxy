from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from gradio_client import Client

app = FastAPI()

# Enable CORS for all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Connect to your Hugging Face Space
client = Client("Ym420/Peptide-Function-Space")   # <-- change if your Space name differs


class SequenceRequest(BaseModel):
    sequence: str


@app.get("/")
def root():
    return {"message": "Peptide proxy server running"}


@app.post("/predict")
def predict(req: SequenceRequest):
    try:
        print("✅ Received peptide sequence:", repr(req.sequence))

        # Call Hugging Face Space API
        result = client.predict(
            sequence=req.sequence,
            api_name="/predict_peptide"     # MUST match Gradio API name
        )

        print("✅ Raw result from HF:", result)

        # result is a list like:
        # [ ["Gram+", 0.8123], ["Fungus", 0.5532], ... ]
        if not isinstance(result, (list, tuple)):
            raise ValueError("Unexpected result format from HF Space")

        parsed = []
        for row in result:
            if isinstance(row, (list, tuple)) and len(row) == 2:
                parsed.append({
                    "target": str(row[0]),
                    "probability": float(row[1])
                })

        print("Parsed predictions:", parsed)
        print("-------------------------")

        return {
            "sequence": req.sequence,
            "predictions": parsed
        }

    except Exception as e:
        print("❌ Error:", str(e))
        return {
            "sequence": req.sequence,
            "predictions": [],
            "error": str(e)
        }
