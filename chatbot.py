import os
import json
import requests
from dotenv import load_dotenv
from typing import Optional, Dict, Any, List

from database import (
    fetch_patient_data,
    get_conversation_history,
    update_conversation_history
)

# Load environment variables
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"


def format_patient_context(patient_context: Optional[Dict[str, Any]]) -> str:
    """Format the additional patient context into a readable prompt string."""
    if not patient_context:
        return ""

    # BMI Calculation
    bmi_info = ""
    try:
        weight = float(patient_context.get('weight', 0))
        height_cm = float(patient_context.get('height', 0))
        if weight and height_cm:
            height_m = height_cm / 100
            bmi = weight / (height_m ** 2)
            bmi_info = f"Weight: {weight} kg, Height: {height_cm} cm, BMI: {bmi:.1f}"
    except (ValueError, ZeroDivisionError):
        pass

    # Format other fields
    symptoms = ", ".join(patient_context.get("symptoms", [])) or "None reported"
    history = patient_context.get("history", "Not provided")
    gender = patient_context.get("gender", "")
    age = patient_context.get("age", "")
    lifestyle = patient_context.get("lifestyle", "Not provided")
    medications = patient_context.get("medications", "None reported")

    return f"""
Additional Patient Context:
- Age: {age}, Gender: {gender}
- {bmi_info}
- Symptoms: {symptoms}
- History: {history}
- Lifestyle: {lifestyle}
- Medications: {medications}
""".strip()


def analyze_report(
        report_id: str,
        custom_prompt: Optional[str] = None,
        patient_context: Optional[Dict[str, Any]] = None
) -> str:
    """
    Generates a medical explanation or response using LLM based on the report.

    Args:
        report_id: Unique ID of the patient's report
        custom_prompt: Optional question the patient asks
        patient_context: Optional additional data for personalization

    Returns:
        LLM-generated message as string
    """
    # Step 1: Fetch patient report from DB
    report_data = fetch_patient_data(report_id)
    if not report_data:
        return "❌ No patient data found for this report ID."

    patient_details = report_data.get("Patient Details", {})
    patient_name = patient_details.get("Name", "there")
    first_name = patient_name.split()[0] if patient_name else "there"
    age = patient_details.get("Age", "unknown age")
    gender = patient_details.get("Gender", "unspecified")

    # Step 2: Format background
    context_str = format_patient_context(patient_context)
    full_report_json = json.dumps(report_data, indent=2)

    background_context = f"""
Patient Info:
Name: {patient_name}
Age: {age}, Gender: {gender}

Lab Report:
{full_report_json}

{context_str}
""".strip()

    # Step 3: System prompt
    system_prompt = f"""
You are Dr. {first_name}'s AI health assistant.
You specialize in analyzing blood test results and explaining them in empathetic, simple language.

ALWAYS follow these:
- Use the patient's first name ({first_name})
- Be warm, positive, and compassionate
- Use analogies and everyday language
- Only greet once (if it's the first message)
- If this is a follow-up, do NOT repeat prior insights unless asked
- Use paragraph breaks for readability
"""

    # Step 4: Assemble messages
    messages: List[Dict[str, str]] = [
        {"role": "system", "content": system_prompt},
        {"role": "system", "content": background_context}
    ]

    # Add chat history if present
    history = get_conversation_history(report_id)
    messages.extend(history)

    if custom_prompt:
        messages.append({"role": "user", "content": custom_prompt})
    else:
        # First-time AI greeting instructions
        messages.append({
            "role": "system",
            "content": (
                f"Start by greeting {first_name} and highlight 1-2 key findings. "
                "Explain them simply, use a helpful analogy, relate any symptoms provided, "
                "and ask how they're feeling. Offer some positive next steps."
            )
        })

    # Step 5: API call
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "llama3-8b-8192",
        "messages": messages,
        "temperature": 0.85,
        "top_p": 0.9,
        "max_tokens": 1000,
        "frequency_penalty": 0.2,
        "presence_penalty": 0.1
    }

    try:
        response = requests.post(GROQ_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        bot_reply = response.json()["choices"][0]["message"]["content"]

        # Store only user-initiated interactions
        if custom_prompt:
            update_conversation_history(report_id, custom_prompt, bot_reply)

        return bot_reply

    except requests.exceptions.RequestException as e:
        return f"Apologies {first_name}, I'm facing technical difficulties reaching the AI model. ({str(e)})"
    except (KeyError, IndexError, json.JSONDecodeError) as e:
        return f"Apologies {first_name}, something went wrong while processing the response. ({str(e)})"
