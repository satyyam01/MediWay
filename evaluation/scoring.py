from sentence_transformers import SentenceTransformer, util
import json

# Load model responses
with open("model_responses.json") as f:
    model_results = json.load(f)

# Load evaluation dataset
with open("evaluation_data.json") as f:
    test_cases = json.load(f)

# Load NLP model for text similarity
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

scores = []

for result in model_results:
    model = result["model"]
    lab_no = result["lab_no"]
    response = result["response"]

    # Get expected response
    expected = next(item["expected_response"] for item in test_cases if item["lab_no"] == lab_no)

    # Compute similarity score
    response_embedding = embedding_model.encode(response, convert_to_tensor=True)
    expected_embedding = embedding_model.encode(expected, convert_to_tensor=True)
    similarity = util.pytorch_cos_sim(response_embedding, expected_embedding).item()

    # Normalize similarity to a 10-point scale
    final_score = round(similarity * 10, 2)

    scores.append({
        "model": model,
        "lab_no": lab_no,
        "similarity_score": final_score
    })

# Save final scores
with open("model_scores.json", "w") as f:
    json.dump(scores, f, indent=2)

print("Model scoring complete!")
