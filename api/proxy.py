# --- proxy.py (Vercel Serverless Function) ---

import json
from gradio_client import Client

# --- Connect to Hugging Face Space ---
# Replace with your actual space path
client = Client("Ym420/peptide-function-classification")

# --- Handler function for Vercel ---
def handler(request, context):
    seq = ""  # Initialize sequence for safety

    try:
        # --- GET request: simple health check ---
        if request.method == "GET":
            return {
                "statusCode": 200,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*"
                },
                "body": json.dumps({"message": "Peptide proxy server running"})
            }

        # --- POST request: call HF Space ---
        if request.method == "POST":
            # Decode and parse JSON body
            data = json.loads(request.body.decode("utf-8"))
            seq = data.get("sequence", "")

            print("✅ Received sequence:", repr(seq))

            # Call Hugging Face Space
            result = client.predict(
                sequence=seq,
                api_name="/predict_peptide"
            )

            # Parse results into standardized format
            parsed = []
            for row in result:
                if isinstance(row, (list, tuple)) and len(row) == 2:
                    parsed.append({
                        "target": str(row[0]),
                        "probability": float(row[1])
                    })

            return {
                "statusCode": 200,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*"
                },
                "body": json.dumps({
                    "sequence": seq,
                    "predictions": parsed
                })
            }

        # --- Unsupported HTTP method ---
        return {
            "statusCode": 405,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({"error": f"Method {request.method} not allowed"})
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({
                "sequence": seq,
                "predictions": [],
                "error": str(e)
            })
        }

