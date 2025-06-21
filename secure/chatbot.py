# chatbot.py
import requests
import json
from database import fetch_patient_data, get_conversation_history, update_conversation_history

GROQ_API_KEY = "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"
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"


def format_patient_context(patient_context):
    """Format patient context information for the AI prompt"""
    if not patient_context:
        return ""

    # Format weight and height for BMI calculation if available
    weight = patient_context.get('weight', '')
    height = patient_context.get('height', '')
    bmi_info = ""
    if weight and height:
        try:
            weight_kg = float(weight)
            height_m = float(height) / 100  # Convert cm to m
            bmi = weight_kg / (height_m * height_m)
            bmi_info = f"BMI: {bmi:.1f} ({weight} kg, {height} cm)"
        except ValueError:
            bmi_info = f"Weight: {weight} kg, Height: {height} cm"

    # Format medical conditions
    medical_conditions = patient_context.get('medical_conditions', [])
    conditions_str = ", ".join(medical_conditions) if medical_conditions else "None reported"

    # Compile context information
    context_info = f"""
    *Additional Patient Context:*
    {bmi_info}
    Medical Conditions: {conditions_str}
    Symptoms: {patient_context.get('symptoms', 'None reported')}
    Lifestyle: {patient_context.get('lifestyle', 'No information provided')}
    Medications: {patient_context.get('medications', 'None reported')}
    """

    return context_info


def analyze_report(lab_no, custom_prompt=None, patient_context=None):
    """
    Fetch patient data and analyze it using Groq API with conversation history.

    Args:
        lab_no: Lab number for the report
        custom_prompt: Optional specific question from the user
        patient_context: Optional additional patient context data
    """
    data = fetch_patient_data(lab_no)
    if not data:
        return {"error": "No patient found with this Lab No."}

    # Get existing conversation history
    conversation_history = get_conversation_history(lab_no)

    # Extract personal details for personalization
    patient_name = data.get('Patient Details', {}).get('Name', 'there')
    patient_age = data.get('Patient Details', {}).get('Age', '')
    patient_gender = data.get('Patient Details', {}).get('Gender', '')

    patient_info = json.dumps(data, indent=2)

    # Process additional patient context
    context_info = format_patient_context(patient_context)

    # System prompt with improved instructions
    system_role = f"""You are Dr. {patient_name.split()[0]}'s Care Assistant, a friendly AI medical companion with a warm, 
    empathetic tone. You specialize in explaining complex medical information in simple, relatable terms. You have Industry Experience of Several Years and it shows in your demeanor.
    Always:
    - Use the patient's first name ({patient_name}) when addressing them 
    - Show genuine concern and maintain positive reinforcement
    - Use conversational language with natural pauses
    - Explain medical terms using everyday analogies
    - Check for understanding periodically
    - Maintain hopeful tone while being honest about risks
    - Use paragraph breaks for readability
    - IMPORTANT: Only greet the patient in your first message. For follow-up messages, respond directly to their question
    - If this is a follow-up message, don't repeat information you've already shared unless asked
    """

    # Build messages array starting with system prompt
    messages = [{"role": "system", "content": system_role}]

    # Add background info as a hidden context message
    background = f"""*Patient Background:*
    {patient_name}, {patient_age} {patient_gender}
    {patient_info}
    {context_info}"""

    messages.append({"role": "system", "content": background})

    # Add conversation history if it exists
    if conversation_history:
        messages.extend(conversation_history)

    # Add the new user message if provided
    if custom_prompt:
        messages.append({"role": "user", "content": custom_prompt})
    else:
        # This is the first message, so add instructions for initial greeting
        instructions = f"""This is the first message to the patient. Begin with a friendly greeting, then:
        1. Mention 1-2 most notable findings in simple terms
        2. Explain one relevant analogy/metaphor
        3. If patient provided context (symptoms, conditions, medications), make specific connections
        4. Ask an open-ended question about their current experience
        5. Suggest clear next steps as options, not commands"""

        messages.append({"role": "system", "content": instructions})

    # API call setup
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "llama3-8b-8192",
        "messages": messages,
        "temperature": 0.85,
        "max_tokens": 1000,
        "top_p": 0.9,
        "frequency_penalty": 0.2,
        "presence_penalty": 0.1
    }

    try:
        response = requests.post(GROQ_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        bot_response = response.json()["choices"][0]["message"]["content"]

        # Save the conversation exchange if it was a real user message
        if custom_prompt:
            update_conversation_history(lab_no, custom_prompt, bot_response)

        return bot_response
    except requests.exceptions.RequestException as e:
        return f"Apologies {patient_name}, I'm experiencing technical difficulties: {str(e)}"
    except (KeyError, IndexError, json.JSONDecodeError) as e:
        return f"Apologies {patient_name}, there was an issue processing your request: {str(e)}"