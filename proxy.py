import json
from gradio_client import Client

# ------------------------------------------------------------
# Create Gradio client ONCE at cold-start.
# This avoids reinitialising the HF Space client per request.
# ------------------------------------------------------------
client = Client("Ym420/peptide-function-classification")


def handler(request, context):
    """
    Main serverless entry point for Vercel.
    Handles:
    - GET "/"       → health check
    - POST "/predict" → forwards to HF Space
    """

    path = request.path        # e.g. "/", "/predict"
    method = request.method    # "GET" or "POST"

    # ------------------------------------------------------------
    # 1. GET "/" — health check endpoint
    # ------------------------------------------------------------
    if path == "/" and method == "GET":
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"message": "Proxy server running OK"})
        }

    # ------------------------------------------------------------
    # 2. POST "/predict" — forwards sequence → HF Space → returns predictions
    # ------------------------------------------------------------
    if path == "/predict" and method == "POST":
        try:
            # Parse JSON request from iOS or browser
            body = json.loads(request.body)
            sequence = body.get("sequence", "")

            print("📥 Received sequence:", sequence)

            # --------------------------------------------------------
            # Call your HF Space API endpoint:
            # app.py contains:
            #     gr.api(predict_peptide, api_name="predict_peptide")
            # So we call `api_name="predict_peptide"`
            # --------------------------------------------------------
            hf_result = client.predict(
                sequence=sequence,
                api_name="predict_peptide"   # ← FIXED (no leading slash)
            )

            print("📤 HF raw result:", hf_result)

            # --------------------------------------------------------
            # Convert HF output (table rows) to JSON for iOS
            # Expected format: [["label1", prob1], ["label2", prob2], ...]
            # --------------------------------------------------------
            predictions = []
            for row in hf_result:
                if isinstance(row, (list, tuple)) and len(row) == 2:
                    predictions.append({
                        "target": str(row[0]),
                        "probability": float(row[1])
                    })

            # Success
            return {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({
                    "sequence": sequence,
                    "predictions": predictions
                })
            }

        except Exception as e:
            print("❌ Error in /predict:", str(e))
            return {
                "statusCode": 500,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({
                    "sequence": sequence,
                    "predictions": [],
                    "error": str(e)
                })
            }

    # ------------------------------------------------------------
    # 3. Any other route → 404 Not Found
    # ------------------------------------------------------------
    return {
        "statusCode": 404,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({
            "error": f"Route '{path}' with method '{method}' not found."
        })
    }
