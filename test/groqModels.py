import requests

GROQ_API_KEY = "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"
GROQ_API_URL = "https://api.groq.com/openai/v1/models"

headers = {
    "Authorization": f"Bearer {GROQ_API_KEY}"
}

response = requests.get(GROQ_API_URL, headers=headers)

if response.status_code == 200:
    print(response.json())  # Prints available models
else:
    print("Error:", response.text)
