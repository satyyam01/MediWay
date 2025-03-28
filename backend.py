from fastapi import FastAPI, Body
from pydantic import BaseModel
from typing import Dict, Any, Optional
from database import fetch_patient_data
from chatbot import analyze_report
from fastapi.routing import APIRoute

app = FastAPI()

for route in app.routes:
    if isinstance(route, APIRoute):
        print(f"Path: {route.path}, Methods: {route.methods}")


class PatientContext(BaseModel):
    patient_context: Dict[str, Any]


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
def get_analysis_get(lab_no: str):
    """Get AI-based insights for a patient's report (GET method)."""
    print(f"Received GET request for lab_no: {lab_no}")  # Debugging
    insights = analyze_report(lab_no)
    return {"lab_no": lab_no, "analysis": insights}


@app.post("/analyze/{lab_no}")
def get_analysis_post(lab_no: str, data: PatientContext):
    """Get AI-based insights for a patient's report with context (POST method)."""
    print(f"Received POST request for lab_no: {lab_no} with context")  # Debugging
    patient_context = data.patient_context
    insights = analyze_report(lab_no, patient_context=patient_context)
    return {"lab_no": lab_no, "analysis": insights}