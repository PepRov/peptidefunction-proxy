import json
from gradio_client import Client
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

# --- HF Space client ---
client = Client("Ym420/peptide-function-classification")  # your working HF Space

def handler(request, context):
    path = request.path
    method = request.method

    # --- GET "/" ---
    if path == "/" and method == "GET":
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"message": "Proxy server running"})
        }

    # --- POST "/predict" ---
    if path == "/predict" and method == "POST":
        try:
            data = json.loads(request.body)
            seq = data.get("sequence", "")
            print("✅ Received sequence:", repr(seq))

            # Call your Gradio HF Space API endpoint
            result = client.predict(sequence=seq, api_name="/predict_peptide")
            print("✅ Raw result from HF:", result)

            # Parse result as in your working code
            parsed = []
            for row in result:
                if isinstance(row, (list, tuple)) and len(row) == 2:
                    parsed.append({"target": str(row[0]), "probability": float(row[1])})

            return {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"sequence": seq, "predictions": parsed})
            }

        except Exception as e:
            print("Error:", str(e))
            return {
                "statusCode": 500,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"sequence": seq, "predictions": [], "error": str(e)})
            }

    # --- Route not found ---
    return {
        "statusCode": 404,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({"error": f"Route {path} with method {method} not found"})
    }
