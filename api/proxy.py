import json
from gradio_client import Client

# connect to your HF Space (public)
client = Client("Ym420/Peptide-Function")  

def handler(request, context):
    try:
        if request.method == "GET":
            return {"message": "Peptide proxy server running"}

        if request.method == "POST":
            body = request.body
            data = json.loads(body)
            seq = data.get("sequence", "")

            result = client.predict(sequence=seq, api_name="/predict_peptide")
            parsed = [{"target": row[0], "probability": float(row[1])} for row in result]

            return {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"sequence": seq, "predictions": parsed})
            }

    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": str(e)})
        }
