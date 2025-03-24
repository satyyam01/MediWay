from fastapi import FastAPI
from database import fetch_patient_data
from chatbot import analyze_report
from fastapi.routing import APIRoute

app = FastAPI()

for route in app.routes:
    if isinstance(route, APIRoute):
        print(f"Path: {route.path}, Methods: {route.methods}")


@app.get("/")
def home():
    return {"message": "Medical Chatbot API is running!"}


@app.get("/report/{lab_no}")
def get_report(lab_no: str):
    """Fetch patient test data."""
    data = fetch_patient_data(lab_no)
    if not data:
        return {"error": "Report not found"}
    return data


@app.get("/analyze/{lab_no}")
def get_analysis(lab_no: str):
    """Get AI-based insights for a patient's report."""
    print(f"Received request for lab_no: {lab_no}")  # Debugging
    insights = analyze_report(lab_no)
    return {"lab_no": lab_no, "analysis": insights}
