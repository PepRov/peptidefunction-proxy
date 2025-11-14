import json

# -------------------------------
# VERCEL SERVERLESS HANDLER
# -------------------------------
def handler(request, context):
    """
    Main entry point for Vercel serverless function.
    Handles GET (health check) and POST (peptide prediction).
    """

    seq = ""  # Initialize safely

    try:
        # -------------------------------
        # GET REQUEST: Health Check
        # -------------------------------
        if request.method == "GET":
            # Return a simple JSON to confirm function is running
            return {
                "statusCode": 200,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*"  # CORS for frontend
                },
                "body": json.dumps({"message": "Peptide proxy server running"})
            }

        # -------------------------------
        # POST REQUEST: Peptide Prediction
        # -------------------------------
        if request.method == "POST":
            # --- Lazy imports ---
            # We import inside the handler to avoid cold-start memory issues
            # and avoid Vercel crashing during module load
            from gradio_client import Client

            # --- Parse JSON body safely ---
            try:
                data = json.loads(request.body.decode("utf-8"))
            except Exception as e:
                print("❌ Failed to parse JSON:", e)
                return {
                    "statusCode": 400,
                    "headers": {"Content-Type": "application/json"},
                    "body": json.dumps({"error": "Invalid JSON"})
                }

            seq = data.get("sequence", "").strip()
            if not seq:
                return {
                    "statusCode": 400,
                    "headers": {"Content-Type": "application/json"},
                    "body": json.dumps({"error": "Missing 'sequence' in request"})
                }

            print("✅ Received sequence:", repr(seq))

            # --- Lazy initialization of HF Client ---
            # We do this here to avoid Vercel crashes on import
            try:
                client = Client("Ym420/peptide-function-classification")
                print("✅ HF Client initialized")
            except Exception as e:
                print("❌ Failed to initialize HF Client:", e)
                return {
                    "statusCode": 500,
                    "headers": {"Content-Type": "application/json"},
                    "body": json.dumps({"sequence": seq, "predictions": [], "error": str(e)})
                }

            # --- Call HF Space API ---
            try:
                # api_name matches what your HF Space defines
                result = client.predict(sequence=seq, api_name="/predict_peptide")
                print("✅ HF Space result:", result)
            except Exception as e:
                print("❌ HF Space predict failed:", e)
                return {
                    "statusCode": 500,
                    "headers": {"Content-Type": "application/json"},
                    "body": json.dumps({"sequence": seq, "predictions": [], "error": str(e)})
                }

            # --- Parse HF result to JSON-friendly format ---
            parsed = []
            for row in result:
                if isinstance(row, (list, tuple)) and len(row) == 2:
                    parsed.append({"target": str(row[0]), "probability": float(row[1])})

            # --- Return predictions ---
            return {
                "statusCode": 200,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*"
                },
                "body": json.dumps({"sequence": seq, "predictions": parsed})
            }

        # -------------------------------
        # Unsupported HTTP methods
        # -------------------------------
        return {
            "statusCode": 405,
            "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
            "body": json.dumps({"error": f"Method {request.method} not allowed"})
        }

    # -------------------------------
    # Catch-all exception handler
    # -------------------------------
    except Exception as e:
        print("❌ Unexpected ERROR:", e)
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
            "body": json.dumps({"sequence": seq, "predictions": [], "error": str(e)})
        }

