# chatbot.py
import requests
import json
import random
import emoji
import datetime
from database import fetch_patient_data, get_conversation_history, update_conversation_history, get_user_preferences, save_user_preferences

GROQ_API_KEY = "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"
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

# Greeting templates for variety
GREETING_TEMPLATES = [
    "Hi {first_name}, I'm your Care Assistant. Good to connect with you today!",
    "Hello {first_name}! I'm your personal Care Assistant here to help you understand your health information.",
    "Welcome, {first_name}! I'm your Care Assistant and I'm here to help you make sense of your health data.",
    "Greetings {first_name}! I'm your friendly Care Assistant - I'm here to explain your medical information clearly.",
    "Nice to meet you, {first_name}! As your Care Assistant, I'm here to assist with your medical questions."
]

# Time-aware greetings
MORNING_GREETINGS = ["Good morning", "Morning", "Rise and shine"]
AFTERNOON_GREETINGS = ["Good afternoon", "Hello this afternoon", "Hope you're having a good afternoon"]
EVENING_GREETINGS = ["Good evening", "Evening", "Hope you're having a nice evening"]

# Emojis for different message types
INFO_EMOJI = "ℹ️"
WARNING_EMOJI = "⚠️"
POSITIVE_EMOJI = "✅"
ACTION_EMOJI = "✨"
QUESTION_EMOJI = "❓"

# Confidence level indicators
CONFIDENCE_HIGH = "🔍 High confidence assessment"
CONFIDENCE_MEDIUM = "🔍 Medium confidence assessment"
CONFIDENCE_LOW = "🔍 Low confidence - please consult your healthcare provider"


def get_time_based_greeting():
    """Return a greeting based on the current time of day"""
    current_hour = datetime.datetime.now().hour

    if 5 <= current_hour < 12:
        return random.choice(MORNING_GREETINGS)
    elif 12 <= current_hour < 18:
        return random.choice(AFTERNOON_GREETINGS)
    else:
        return random.choice(EVENING_GREETINGS)


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


def analyze_sentiment(message):
    """Simple sentiment analysis to adjust tone"""
    if not message:
        return "neutral"

    # Simple keyword-based sentiment analysis
    worried_words = ["worried", "scared", "anxious", "stress", "fear", "concerning", "nervous"]
    urgent_words = ["urgent", "immediately", "emergency", "critical", "severe", "pain", "hurts"]
    positive_words = ["good", "better", "improving", "happy", "glad", "positive", "hopeful"]

    message = message.lower()

    if any(word in message for word in worried_words):
        return "concerned"
    elif any(word in message for word in urgent_words):
        return "urgent"
    elif any(word in message for word in positive_words):
        return "positive"
    else:
        return "neutral"


def format_action_items(text):
    """Format action items in the response to make them stand out"""
    lines = text.split('\n')
    formatted_lines = []

    for line in lines:
        if any(action_phrase in line.lower() for action_phrase in
               ["next steps", "recommend", "should", "advised to", "action items", "follow up"]):
            formatted_lines.append(f"\n{ACTION_EMOJI} **ACTION ITEM:** {line}\n")
        else:
            formatted_lines.append(line)

    return '\n'.join(formatted_lines)


def add_progress_indicator(is_first_message):
    """Add a progress indicator for the analysis process"""
    if is_first_message:
        return "\n\n*Analysis Progress: Initial assessment complete. Further discussion may reveal more insights.*"
    else:
        return ""


def generate_follow_up_prompts(data, conversation_history):
    """Generate contextual follow-up prompts based on the data and conversation history"""
    prompts = []

    # Check if certain topics have been discussed
    topics_discussed = ' '.join([msg.get('content', '') for msg in conversation_history])

    # Check for abnormal values in data
    abnormal_tests = []
    if 'Test Results' in data:
        for test, result in data['Test Results'].items():
            if 'abnormal' in str(result).lower() or 'high' in str(result).lower() or 'low' in str(result).lower():
                abnormal_tests.append(test)

    # Generate follow-up prompts
    if abnormal_tests and 'explain' not in topics_discussed.lower():
        prompts.append(f"Could you explain more about my {random.choice(abnormal_tests)} result?")

    if 'treatment' not in topics_discussed.lower():
        prompts.append("What treatment options should I consider?")

    if 'lifestyle' not in topics_discussed.lower():
        prompts.append("Are there lifestyle changes that could help with these results?")

    if 'next steps' not in topics_discussed.lower():
        prompts.append("What should my next steps be?")

    # Return a random selection of 2 prompts if we have enough
    if len(prompts) > 2:
        return random.sample(prompts, 2)
    return prompts


def post_process_response(response, sentiment, is_first_message, data, conversation_history):
    """Post-process the AI response to enhance UX"""
    # Add summary card for important information
    if is_first_message:
        summary = "**KEY FINDINGS SUMMARY:**\n"
        summary += "• This is a computer-generated summary of your results\n"

        # Extract abnormal findings
        abnormal_findings = []
        if 'Test Results' in data:
            for test, result in data['Test Results'].items():
                if 'abnormal' in str(result).lower() or 'high' in str(result).lower() or 'low' in str(result).lower():
                    abnormal_findings.append(f"{test}: {result}")

        if abnormal_findings:
            summary += "• Attention areas: " + ", ".join(abnormal_findings[:2])
            if len(abnormal_findings) > 2:
                summary += " and others"
            summary += "\n"
        else:
            summary += "• No significant abnormalities detected\n"

        summary += "\n---\n\n"
        response = summary + response

    # Format action items
    response = format_action_items(response)

    # Add confidence indicator based on sentiment and response content
    if "uncertain" in response.lower() or "not sure" in response.lower():
        confidence = CONFIDENCE_LOW
    elif "likely" in response.lower() or "possibly" in response.lower():
        confidence = CONFIDENCE_MEDIUM
    else:
        confidence = CONFIDENCE_HIGH

    # Add follow-up prompts
    follow_ups = generate_follow_up_prompts(data, conversation_history)
    if follow_ups:
        response += "\n\n**Some questions you might want to ask:**\n"
        for prompt in follow_ups:
            response += f"• {prompt}\n"

    # Add progress indicator
    response += add_progress_indicator(is_first_message)

    # Add confidence indicator
    response += f"\n\n{confidence}"

    return response


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

    # Get user preferences if available
    user_preferences = get_user_preferences(lab_no) or {
        "communication_style": "simple",  # simple or technical
        "response_length": "balanced"  # brief, balanced, or detailed
    }

    # Extract personal details for personalization
    patient_name = data.get('Patient Details', {}).get('Name', 'there')
    first_name = patient_name.split()[0] if patient_name != 'there' else 'there'
    patient_age = data.get('Patient Details', {}).get('Age', '')
    patient_gender = data.get('Patient Details', {}).get('Gender', '')

    # Determine if this is the first message
    is_first_message = not conversation_history and not custom_prompt

    # Get time-aware greeting
    time_greeting = get_time_based_greeting()

    # Analyze sentiment if there's a custom prompt
    sentiment = "neutral"
    if custom_prompt:
        sentiment = analyze_sentiment(custom_prompt)

    patient_info = json.dumps(data, indent=2)

    # Process additional patient context
    context_info = format_patient_context(patient_context)

    # System prompt with improved instructions based on user preferences and sentiment
    system_role = f"""You are Dr. {first_name}'s Care Assistant, a friendly AI medical companion with a warm, 
    empathetic tone. You specialize in explaining complex medical information in simple, relatable terms. You have Industry Experience of Several Years and it shows in your demeanor.

    Always:
    - Use the patient's first name ({first_name}) when addressing them 
    - Show genuine concern and maintain positive reinforcement
    - Use conversational language with natural pauses
    - Explain medical terms using everyday analogies
    - Check for understanding periodically
    - Maintain hopeful tone while being honest about risks
    - Use paragraph breaks for readability
    - IMPORTANT: Only greet the patient in your first message. For follow-up messages, respond directly to their question
    - If this is a follow-up message, don't repeat information you've already shared unless asked

    Current user preferences:
    - Communication style: {user_preferences['communication_style']} (use {'simple language and analogies' if user_preferences['communication_style'] == 'simple' else 'more technical medical terminology'})
    - Response length: {user_preferences['response_length']} (provide {'brief answers' if user_preferences['response_length'] == 'brief' else 'detailed explanations' if user_preferences['response_length'] == 'detailed' else 'balanced responses'})

    Current user sentiment: {sentiment} (be {'extra reassuring' if sentiment == 'concerned' else 'direct and clear' if sentiment == 'urgent' else 'positive and encouraging' if sentiment == 'positive' else 'balanced and informative'})

    When formatting your response:
    - Use markdown formatting for emphasis (**bold** for important points, *italics* for medical terms)
    - Use bullet points (•) for lists
    - Use headings (## or ###) for sections
    - Add a visual indicator before warnings ({WARNING_EMOJI}) and positive news ({POSITIVE_EMOJI})
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
        # This is the first message, so add instructions for initial greeting with time awareness
        greeting = random.choice(GREETING_TEMPLATES).format(first_name=first_name)
        greeting = f"{time_greeting}, {greeting}"

        instructions = f"""This is the first message to the patient. Begin with this greeting: "{greeting}" Then:
        1. Mention 1-2 most notable findings in simple terms
        2. Explain one relevant analogy/metaphor
        3. If patient provided context (symptoms, conditions, medications), make specific connections
        4. Ask an open-ended question about their current experience
        5. Suggest clear next steps as options, not commands
        6. Format your response with markdown for readability
        7. Use {POSITIVE_EMOJI} for positive findings and {WARNING_EMOJI} for findings that need attention"""

        messages.append({"role": "system", "content": instructions})

    # API call setup
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    # Adjust model parameters based on preferences
    temperature = 0.85
    if user_preferences['communication_style'] == 'technical':
        temperature = 0.7  # More precise for technical communication

    max_tokens = 1000
    if user_preferences['response_length'] == 'brief':
        max_tokens = 500
    elif user_preferences['response_length'] == 'detailed':
        max_tokens = 1500

    payload = {
        "model": "llama3-8b-8192",
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "top_p": 0.9,
        "frequency_penalty": 0.2,
        "presence_penalty": 0.1
    }

    try:
        response = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        bot_response = response.json()["choices"][0]["message"]["content"]

        # Post-process response to enhance UX
        enhanced_response = post_process_response(bot_response, sentiment, is_first_message, data, conversation_history)

        # Save the conversation exchange if it was a real user message
        if custom_prompt:
            update_conversation_history(lab_no, custom_prompt, enhanced_response)

        return enhanced_response
    except requests.exceptions.RequestException as e:
        return f"{WARNING_EMOJI} Apologies {first_name}, I'm experiencing technical difficulties: {str(e)}"
    except (KeyError, IndexError, json.JSONDecodeError) as e:
        return f"{WARNING_EMOJI} Apologies {first_name}, there was an issue processing your request: {str(e)}"


def update_user_preferences(lab_no, preferences):
    """Update user preferences for communication"""
    try:
        save_user_preferences(lab_no, preferences)
        return {"success": "Preferences updated successfully"}
    except Exception as e:
        return {"error": f"Failed to update preferences: {str(e)}"}