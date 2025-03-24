import requests
import json
from database import fetch_patient_data

GROQ_API_KEY = "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"
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"


def analyze_report(lab_no, custom_prompt=None, patient_context=None):
    """
    Fetch patient data and analyze it using Groq API with enhanced conversational prompts.
    Now includes optional patient context for more personalized insights.

    Args:
        lab_no: Lab number for the report
        custom_prompt: Optional specific question from the user
        patient_context: Optional additional patient context data
    """
    data = fetch_patient_data(lab_no)
    if not data:
        return {"error": "No patient found with this Lab No."}

    # Extract personal details for personalization
    patient_name = data.get('Patient Details', {}).get('Name', 'there')
    patient_age = data.get('Patient Details', {}).get('Age', '')
    patient_gender = data.get('Patient Details', {}).get('Gender', '')

    patient_info = json.dumps(data, indent=2)

    # Process additional patient context if available
    context_info = ""
    if patient_context:
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

    # Base persona setup
    system_role = f"""You are Dr. {patient_name.split()[0]}'s Care Assistant, a friendly AI medical companion with a warm, 
    empathetic tone. You specialize in explaining complex medical information in simple, relatable terms. 
    Always:
    - Use the patient's name ({patient_name}) when addressing them
    - Show genuine concern and maintain positive reinforcement
    - Use conversational language with natural pauses (e.g., "Let's see...", "Hmm, I notice that...")
    - Explain medical terms using everyday analogies
    - Check for understanding periodically
    - Maintain hopeful tone while being honest about risks
    - Use paragraph breaks for readability
    - When patient context is available, reference relevant lifestyle factors, symptoms, medical conditions or medications that might affect the results"""

    if custom_prompt:
        prompt = f"""*Patient Background:*
        {patient_name}, {patient_age} {patient_gender}
        {patient_info}
        {context_info}

        *Current Conversation:*
        User asks: "{custom_prompt}"

        Respond as if talking to a friend:
        1. Acknowledge their concern with empathy
        2. Answer clearly with 1-2 key points max
        3. Offer to explain further or discuss next steps
        4. Use relatable examples (e.g., "This vitamin level is like your car's...")
        5. If their question relates to any provided medical conditions, medications, or symptoms, make specific connections
        """
    else:
        prompt = f"""*New Patient Report Review:*
        {patient_name}, {patient_age} {patient_gender}
        {patient_info}
        {context_info}

        *Your Task:*
        Initiate conversation by:
        1. Friendly greeting using their name
        2. Mention 1-2 most notable findings in simple terms, relate to any provided medical conditions if relevant
        3. Explain one relevant analogy/metaphor
        4. If patient provided context (symptoms, conditions, medications), make specific connections to test results
        5. Ask an open-ended question about their current experience
        6. Suggest clear next steps as options, not commands

        Example structure:
        "Hi {patient_name}, I've reviewed your results along with the additional information you provided. Let's start with what's most important...
        [Simple explanation] This is similar to [everyday analogy]...
        I noticed you mentioned [symptom/condition] - this relates to your results because...
        How does this align with how you've been feeling lately?" 
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
        "temperature": 0.85,  # Slightly higher for creativity
        "max_tokens": 1000,
        "top_p": 0.9,
        "frequency_penalty": 0.2,  # Reduce repetition
        "presence_penalty": 0.1
    }

    try:
        response = requests.post(GROQ_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        raw_response = response.json()["choices"][0]["message"]["content"]

        # Add conversational formatting
        return raw_response.replace(". ", ".  ")  # Add spacing for better readability
    except requests.exceptions.RequestException as e:
        return f"Apologies {patient_name}, I'm experiencing technical difficulties. Please try again in a moment."
    except (KeyError, IndexError, json.JSONDecodeError) as e:
        return f"Looks like something went sideways. Could you rephrase your question?"