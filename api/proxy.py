import json
from gradio_client import Client

# --- Connect to Hugging Face Space (public) ---
try:
    client = Client("Ym420/peptide-function-classification")
    print("✅ Connected to HF Space successfully")
except Exception as e:
    print("❌ Failed to connect to HF Space:", e)
    client = None

# --- Vercel handler ---
def handler(request, context):
    seq = ""  # Initialize safely

    try:
        # --- GET: health check ---
        if request.method == "GET":
            return {
                "statusCode": 200,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*"
                },
                "body": json.dumps({"message": "Peptide proxy server running"})
            }

        # --- POST: predict peptide ---
        if request.method == "POST":
            if client is None:
                raise RuntimeError("HF Space client not initialized")

            data = json.loads(request.body.decode("utf-8"))
            seq = data.get("sequence", "")

            if not seq:
                return {
                    "statusCode": 400,
                    "headers": {
                        "Content-Type": "application/json",
                        "Access-Control-Allow-Origin": "*"
                    },
                    "body": json.dumps({"error": "Missing 'sequence' in request"})
                }

            print("✅ Received sequence:", repr(seq))

            result = client.predict(sequence=seq, api_name="/predict_peptide")
            print("✅ HF Space result:", result)

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

        # --- Unsupported method ---
        return {
            "statusCode": 405,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({"error": f"Method {request.method} not allowed"})
        }

    except Exception as e:
        print("❌ ERROR:", e)
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
