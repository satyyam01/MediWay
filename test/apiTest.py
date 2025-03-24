import requests

response = requests.get("http://127.0.0.1:8000/analyze/182387104")
print(response.status_code, response.text)
