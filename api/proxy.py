import json
from gradio_client import Client

client = Client("Ym420/peptide-function-classification")  # HF Space

def handler(request, context):
    if request.method == "GET":
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"message": "Proxy server running"})
        }

    if request.method == "POST":
        try:
            data = json.loads(request.body)
            seq = data.get("sequence", "")
            print("✅ Received sequence:", repr(seq))

            # Call HF Space
            result = client.predict(sequence=seq, api_name="/predict_promoter")
            print("✅ Raw result from HF:", result)

            if isinstance(result, (list, tuple)) and len(result) >= 2:
                label = str(result[0])
                confidence = float(result[1])
            else:
                label = "error"
                confidence = 0.0

            return {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({
                    "sequence": seq,
                    "prediction": label,
                    "confidence": confidence
                })
            }

        except Exception as e:
            print("Error:", str(e))
            return {
                "statusCode": 500,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({
                    "sequence": seq,
                    "prediction": "error",
                    "confidence": 0.0,
                    "error": str(e)
                })
            }

    return {
        "statusCode": 405,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({"error": f"Method {request.method} not allowed"})
    }


