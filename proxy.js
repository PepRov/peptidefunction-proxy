export const config = {
  runtime: "edge"
};

export default async function handler(req) {
  try {
    if (req.method === "GET") {
      return new Response(
        JSON.stringify({ message: "Proxy server running" }),
        { status: 200, headers: { "Content-Type": "application/json" } }
      );
    }

    if (req.method !== "POST") {
      return new Response("Method not allowed", { status: 405 });
    }

    const body = await req.json();
    const sequence = body.sequence || "";

    console.log("Received sequence:", sequence);

    // --- HF SPACE URL (equivalent to your gradio_client call) ---
    const HF_URL =
      "https://Ym420-peptide-function-classification.hf.space/predict_peptide";

    // --- Call HF Space ---
    const hfRes = await fetch(HF_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ sequence })
    });

    const result = await hfRes.json();
    console.log("HF raw result:", result);

    // --- Normalise prediction output ---
    let predictions = [];

    // Case 1: Gradio DataFrame format
    if (result && result.data) {
      for (const row of result.data) {
        predictions.push({
          target: row[0],
          probability: parseFloat(row[1])
        });
      }
    }

    // Case 2: Simple list of lists
    else if (Array.isArray(result)) {
      for (const row of result) {
        predictions.push({
          target: row[0],
          probability: parseFloat(row[1])
        });
      }
    }

    return new Response(
      JSON.stringify({
        sequence,
        predictions
      }),
      {
        status: 200,
        headers: {
          "Content-Type": "application/json",
          "Access-Control-Allow-Origin": "*"
        }
      }
    );
  } catch (err) {
    console.error("Error in /predict:", err);

    return new Response(
      JSON.stringify({
        sequence: "",
        predictions: [],
        error: String(err)
      }),
      { status: 500, headers: { "Content-Type": "application/json" } }
    );
  }
}
