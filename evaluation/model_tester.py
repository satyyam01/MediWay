import requests
import json
import time
import logging

# Logging setup
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Groq API Key & URL
GROQ_API_KEY = "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"
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

# Models to test
models_to_test = [
    "llama3-70b-8192",
    "deepseek-r1-distill-llama-70b",
    "qwen-2.5-32b",
    "llama-3.3-70b-specdec",
    "llama-3.2-11b-Vision-Preview",
    "mistral-saba-24b",  # Strong alternative to Mixtral
    "llama3-8b-8192",  # Smaller but efficient
    "qwen-2.5-coder-32b",  # May help with structured medical reasoning
    "gemma2-9b-it"  # Google's fine-tuned model
]

# Load test cases
with open("evaluation_data.json") as f:
    test_cases = json.load(f)

results = []

for model in models_to_test:
    logging.info(f"Testing model: {model}")

    for case in test_cases:
        lab_no = case["lab_no"]
        question = case["question"]

        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": "You are a medical AI expert analyzing blood test reports."},
                {"role": "user", "content": f"Patient Report (Lab No: {lab_no}).\nUser Question: {question}"}
            ],
            "temperature": 0.5,
            "max_tokens": 1000
        }

        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(GROQ_API_URL, headers=headers, json=payload)
            response_json = response.json()

            if "choices" in response_json:
                model_response = response_json["choices"][0]["message"]["content"]
            else:
                model_response = f"Error: {response_json.get('error', 'Unknown API issue')}"

        except Exception as e:
            model_response = f"Error: {str(e)}"

        results.append({
            "model": model,
            "lab_no": lab_no,
            "question": question,
            "response": model_response
        })

        logging.info(f"Model {model} - Lab No: {lab_no} - Response saved")

        # Avoid rate limiting issues
        time.sleep(1)

# Save results to JSON
with open("model_responses.json", "w") as f:
    json.dump(results, f, indent=2)

logging.info("All model responses saved successfully!")
