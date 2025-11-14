# --- proxy.py (Option 1 for Vercel Serverless Function) ---

import json
from gradio_client import Client

# --- Connect to Hugging Face Space ---
client = Client("Ym420/peptide-function-classification")  # MODIFIED: kept from your original

# --- Handler function for Vercel ---
# MODIFIED: Replaced FastAPI app with single handler(request, context)
def handler(request, context):
    # --- GET request ---
    if request.method == "GET":
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"message": "Peptide proxy server running"})  # MODIFIED: replaces FastAPI root()
        }

    # --- POST request ---
    if request.method == "POST":
        try:
            # MODIFIED: replaced FastAPI BaseModel with manual JSON parsing
            data = json.loads(request.body)
            seq = data.get("sequence", "")

            print("✅ Received sequence:", repr(seq))  # MODIFIED: kept debug print

            # Call HF Space API
            result = client.predict(
                sequence=seq,
                api_name="/predict_peptide"
            )

            # Parse results
            parsed = []
            for row in result:
                if isinstance(row, (list, tuple)) and len(row) == 2:
                    parsed.append({
                        "target": str(row[0]),
                        "probability": float(row[1])
                    })

            return {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({
                    "sequence": seq,
                    "predictions": parsed
                })
            }

        except Exception as e:
            return {
                "statusCode": 500,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({
                    "sequence": seq,
                    "predictions": [],
                    "error": str(e)
                })
            }

