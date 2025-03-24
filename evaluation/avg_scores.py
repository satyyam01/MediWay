import json
from collections import defaultdict


def average_scores(input_file, output_file):
    with open(input_file, "r") as f:
        data = json.load(f)

    score_sums = defaultdict(float)
    count = defaultdict(int)

    # Aggregate scores for each model
    for entry in data:
        model = entry["model"]
        score_sums[model] += entry["similarity_score"]
        count[model] += 1

    # Compute averages
    avg_scores = [
        {"model": model, "average_similarity_score": score_sums[model] / count[model]}
        for model in score_sums
    ]

    # Save results
    with open(output_file, "w") as f:
        json.dump(avg_scores, f, indent=4)

    print(f"Averaged scores saved to {output_file}")


# Example usage
average_scores("model_scores.json", "model_scores_avg.json")
