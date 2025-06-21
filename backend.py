from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
from pymongo import MongoClient
from chatbot import analyze_report
import os

# ------------------------- MongoDB Setup -------------------------
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
client = MongoClient(MONGO_URI)
db = client["mediway"]

patients_collection = db["patients"]
tests_collection = db["tests"]
conversations_collection = db["conversations"]

# ------------------------- FastAPI App Setup -------------------------
app = FastAPI(
    title="MediWay AI Assistant API",
    description="Backend service for AI-powered blood report insights",
    version="1.0.0"
)

# Allow frontend (e.g., Streamlit app) to access this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For production, change to only frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# ------------------------- Request Models -------------------------
class PatientContext(BaseModel):
    patient_context: Dict[str, Any]

class UserMessage(BaseModel):
    message: str
    patient_context: Optional[Dict[str, Any]] = None

# ------------------------- Utility Functions -------------------------
def fetch_patient_data(report_id: str) -> Optional[Dict[str, Any]]:
    patient = patients_collection.find_one({"report_id": report_id})
    if not patient:
        return None

    tests = list(tests_collection.find({"report_id": report_id}))

    return {
        "Patient Details": {
            "Name": patient.get("name"),
            "Age": patient.get("age"),
            "Gender": patient.get("gender"),
            "Collected Date": patient.get("collected_date"),
            "Reported Date": patient.get("reported_date")
        },
        "Tests": [
            {
                "Name": test.get("test_name"),
                "Value": test.get("result"),
                "Unit": test.get("unit"),
                "Reference Interval": test.get("reference_interval")
            } for test in tests
        ]
    }

def clear_conversation_history(report_id: str):
    conversations_collection.delete_many({"report_id": report_id})

# ------------------------- API Routes -------------------------

@app.get("/", tags=["Status"])
def home():
    return {
        "message": "MediWay AI Assistant API is running!",
        "status": "active"
    }

@app.get("/report/{report_id}", tags=["Report"])
def get_report(report_id: str):
    data = fetch_patient_data(report_id)
    if not data:
        raise HTTPException(status_code=404, detail="❌ Report not found.")
    return data

@app.get("/analyze/{report_id}", tags=["Analysis"])
def get_initial_analysis(report_id: str):
    data = fetch_patient_data(report_id)
    if not data:
        raise HTTPException(status_code=404, detail="❌ Report not found.")

    analysis = analyze_report(report_id)
    return {
        "report_id": report_id,
        "analysis": analysis
    }

@app.post("/analyze/{report_id}", tags=["Analysis"])
def analyze_with_context(report_id: str, payload: PatientContext):
    data = fetch_patient_data(report_id)
    if not data:
        raise HTTPException(status_code=404, detail="❌ Report not found.")

    analysis = analyze_report(report_id, patient_context=payload.patient_context)
    return {
        "report_id": report_id,
        "analysis": analysis
    }

@app.post("/chat/{report_id}", tags=["Chat"])
def chat(report_id: str, payload: UserMessage):
    data = fetch_patient_data(report_id)
    if not data:
        raise HTTPException(status_code=404, detail="❌ Report not found.")

    response = analyze_report(
        report_id,
        custom_prompt=payload.message,
        patient_context=payload.patient_context
    )
    return {
        "report_id": report_id,
        "response": response
    }

@app.delete("/chat/{report_id}", tags=["Chat"])
def reset_chat(report_id: str):
    clear_conversation_history(report_id)
    return {
        "report_id": report_id,
        "status": "🗑️ Conversation history cleared."
    }
