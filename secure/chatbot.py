import requests
import json
from database import fetch_patient_data

GROQ_API_KEY = "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"
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"


def analyze_report(lab_no, custom_prompt=None):
    """
    Fetch patient data and analyze it using Qwen API with enhanced conversational prompts.
    """
    data = fetch_patient_data(lab_no)
    if not data:
        return {"error": "No patient found with this Lab No."}

    # Extract personal details for a friendly approach
    patient_name = data.get('name', 'there')
    patient_age = data.get('age', '')
    patient_gender = data.get('gender', '')

    patient_info = json.dumps(data, indent=2)

    # System role to ensure an engaging & reassuring response
    system_role = f"""
    You are Dr. {patient_name.split()[0]}'s AI Medical Assistant, specializing in making blood test reports easier to understand. 
    Your responses should:
    - Address {patient_name} personally
    - Use an empathetic, encouraging tone
    - Break down medical terms into simple explanations
    - Use analogies that relate to everyday life (e.g., "Think of hemoglobin like oxygen delivery trucks in your body.")
    - Offer insights but avoid making absolute diagnoses
    - Ask open-ended questions to encourage patient engagement
    """

    # Choose appropriate prompt
    if custom_prompt:
        prompt = f"""
        *Patient Background:*
        Name: {patient_name}, Age: {patient_age}, Gender: {patient_gender}
        {patient_info}

        *User's Query:*  
        "{custom_prompt}"  

        *Response Guidelines:*  
        1. Start with an empathetic acknowledgment  
        2. Answer in **2-3 concise, clear points**  
        3. Use a relatable analogy if applicable  
        4. Ask if they need further clarification  
        """
    else:
        prompt = f"""
        *Blood Test Analysis for {patient_name} ({patient_age}, {patient_gender})*

        *Main Findings:*  
        {patient_info}  

        *Your Task:*  
        - Greet {patient_name} warmly  
        - Highlight **one or two key findings** in easy terms  
        - Use a simple analogy to explain a key result  
        - Ask them how they’ve been feeling in relation to the report  
        - Offer **next steps in a friendly, non-alarming way**  

        **Example start:**  
        "Hi {patient_name}, I just went through your blood test results.  Here’s something that stood out...  
        [Explain finding] – it’s kind of like [use analogy]...  
        Have you been feeling [related symptom] recently?"  
        """

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "qwen-2.5-coder-32b",
        "messages": [
            {"role": "system", "content": system_role},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.8,  # Keeps responses engaging but not too unpredictable
        "max_tokens": 1000,
        "top_p": 0.9,
        "frequency_penalty": 0.2,  # Helps reduce repeated information
        "presence_penalty": 0.1
    }

    try:
        response = requests.post(GROQ_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        raw_response = response.json()["choices"][0]["message"]["content"]

        # Improve readability by adding natural pauses
        return raw_response.replace(". ", ".  ")

    except requests.exceptions.RequestException:
        return f"Apologies {patient_name}, I'm having trouble connecting. Please try again in a moment."

    except (KeyError, IndexError, json.JSONDecodeError):
        return "Something went wrong on my end. Could you try asking again?"

