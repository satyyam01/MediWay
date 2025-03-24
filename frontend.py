import streamlit as st
import os
import tempfile
import requests
import time
import json
from PIL import Image
from preprocessing import MedicalReportProcessor
from auth import StreamlitAuth, login_required, display_login_form, logout

# API endpoints
API_BASE_URL = "http://127.0.0.1:8080"  # FastAPI base URL


def save_uploaded_file(uploaded_file):
    """Save uploaded file to a temporary location and return the path"""
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
        tmp_file.write(uploaded_file.getvalue())
        return tmp_file.name


def process_pdf(file_path):
    """Process the uploaded PDF using MedicalReportProcessor"""
    processor = MedicalReportProcessor(db_name="medical_reports_new.db")
    success = processor.process_report(file_path)

    # Check if data is stored
    conn = processor._get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT lab_no FROM Patients ORDER BY id DESC LIMIT 1")
    result = cursor.fetchone()
    cursor.close()
    conn.close()

    if result:
        print("Retrieved lab_no:", result[0])  # Debugging
        return success, result[0]
    else:
        print("No lab_no found!")  # Debugging
        return success, None


def fetch_report_data(lab_no):
    """Fetch report data from FastAPI endpoint"""
    try:
        response = requests.get(f"{API_BASE_URL}/report/{lab_no}")
        print("Fetching report data:", response.status_code, response.text)  # Debug print
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error fetching report: {response.text}")
            return None
    except Exception as e:
        st.error(f"API connection error: {e}")
        return None


def get_analysis(lab_no, patient_context=None):
    """Get AI analysis for the report with optional patient context"""
    try:
        with st.spinner("Analyzing report with AI..."):
            if patient_context:
                # Send patient context along with the analysis request
                response = requests.post(
                    f"{API_BASE_URL}/analyze/{lab_no}",
                    json={"patient_context": patient_context}
                )
            else:
                response = requests.get(f"{API_BASE_URL}/analyze/{lab_no}")

            print("Fetching AI analysis:", response.status_code, response.text)  # Debug print
            if response.status_code == 200:
                return response.json()["analysis"]
            else:
                st.error(f"Error getting analysis: {response.text}")
                return None
    except Exception as e:
        st.error(f"AI analysis error: {e}")
        return None


def display_patient_form():
    """Display the patient context form and return the collected data"""
    with st.expander("Patient Information Form", expanded=True):
        st.write("Please provide additional information to help us analyze your results better.")

        # Initialize the form data in session state if not already present
        if "patient_context" not in st.session_state:
            st.session_state.patient_context = {
                "weight": "",
                "height": "",
                "medical_conditions": [],
                "symptoms": "",
                "lifestyle": "",
                "medications": ""
            }

        # Basic information
        col1, col2 = st.columns(2)
        with col1:
            weight = st.text_input("Weight (kg)", value=st.session_state.patient_context.get("weight", ""))
        with col2:
            height = st.text_input("Height (cm)", value=st.session_state.patient_context.get("height", ""))

        # Medical conditions with checkboxes
        st.subheader("Medical Conditions")
        col1, col2 = st.columns(2)

        with col1:
            diabetes = st.checkbox("Diabetes",
                                   value="Diabetes" in st.session_state.patient_context.get("medical_conditions", []))
            hypertension = st.checkbox("High Blood Pressure",
                                       value="High Blood Pressure" in st.session_state.patient_context.get(
                                           "medical_conditions", []))
            heart_disease = st.checkbox("Heart Disease", value="Heart Disease" in st.session_state.patient_context.get(
                "medical_conditions", []))

        with col2:
            thyroid = st.checkbox("Thyroid Issues",
                                  value="Thyroid Issues" in st.session_state.patient_context.get("medical_conditions",
                                                                                                 []))
            kidney_disease = st.checkbox("Kidney Disease",
                                         value="Kidney Disease" in st.session_state.patient_context.get(
                                             "medical_conditions", []))
            liver_disease = st.checkbox("Liver Disease", value="Liver Disease" in st.session_state.patient_context.get(
                "medical_conditions", []))

        # Other conditions
        other_conditions = st.text_input("Other Medical Conditions",
                                         value=st.session_state.patient_context.get("other_conditions", ""))

        # Current symptoms
        symptoms = st.text_area("Current Symptoms",
                                value=st.session_state.patient_context.get("symptoms", ""))

        # Lifestyle information
        lifestyle = st.text_area("Lifestyle Information (diet, exercise, smoking, alcohol, etc.)",
                                 value=st.session_state.patient_context.get("lifestyle", ""))

        # Current medications
        medications = st.text_area("Current Medications",
                                   value=st.session_state.patient_context.get("medications", ""))

        # Submit button
        if st.button("Save Information"):
            # Gather medical conditions
            medical_conditions = []
            if diabetes:
                medical_conditions.append("Diabetes")
            if hypertension:
                medical_conditions.append("High Blood Pressure")
            if heart_disease:
                medical_conditions.append("Heart Disease")
            if thyroid:
                medical_conditions.append("Thyroid Issues")
            if kidney_disease:
                medical_conditions.append("Kidney Disease")
            if liver_disease:
                medical_conditions.append("Liver Disease")

            if other_conditions:
                medical_conditions.extend([c.strip() for c in other_conditions.split(',')])

            # Save to session state
            st.session_state.patient_context = {
                "weight": weight,
                "height": height,
                "medical_conditions": medical_conditions,
                "other_conditions": other_conditions,
                "symptoms": symptoms,
                "lifestyle": lifestyle,
                "medications": medications
            }

            st.success("Patient information saved successfully!")
            return True

    return False


@login_required
def display_report_and_insights(report_data, lab_no):
    """Display the report data and AI insights"""
    # Patient details
    st.header("Patient Information")
    patient = report_data["Patient Details"]

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**Name:** {patient['Name']}")
        st.markdown(f"**Age:** {patient['Age']}")
        st.markdown(f"**Gender:** {patient['Gender']}")
    with col2:
        st.markdown(f"**Lab Number:** {patient['Lab Number']}")
        st.markdown(f"**Sample Collected:** {patient['Collected Date']}")
        st.markdown(f"**Report Date:** {patient['Reported Date']}")

    # Test results
    st.header("Test Results")

    # Create a DataFrame for the test results
    import pandas as pd
    test_data = []
    for test in report_data["Tests"]:
        test_data.append({
            "Test Name": test["Name"],
            "Result": test["Value"],
            "Unit": test["Unit"],
            "Reference Range": test["Reference Interval"]
        })

    df = pd.DataFrame(test_data)
    st.dataframe(df, use_container_width=True)

    # Get and display AI analysis
    st.header("AI Analysis")

    # Check if we already have analysis in session state
    analysis_key = f"analysis_{lab_no}"
    if analysis_key not in st.session_state:
        # Pass patient context to analysis if available
        analysis = get_analysis(lab_no, st.session_state.get("patient_context"))
        if analysis:
            st.session_state[analysis_key] = analysis

    if analysis_key in st.session_state:
        st.markdown(st.session_state[analysis_key])

    # Chatbot interface
    st.header("Chat with MediWay")

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant",
             "content": "Hello! I'm your medical assistant. You can ask me questions about your blood test results."}
        ]

    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    if prompt := st.chat_input("Ask about your test results..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate assistant response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                # Create context with report data, patient context, and chat history
                patient_context = st.session_state.get("patient_context", {})
                context = {
                    "report_data": report_data,
                    "patient_context": patient_context,
                    "prompt": prompt
                }

                # Here we would normally make a call to the chatbot API with the context
                # For now, we'll simulate it with a direct call to analyze_report
                from chatbot import analyze_report

                # Create a more focused prompt based on the user's question and patient context
                response = analyze_report(lab_no, custom_prompt=prompt, patient_context=patient_context)

                # Display the response
                st.markdown(response)

                # Add assistant response to chat history
                st.session_state.messages.append({"role": "assistant", "content": response})


def main():
    # Set page config
    st.set_page_config(
        page_title="MediWay - Blood Report Analysis",
        page_icon="🩸",
        layout="wide"
    )

    # App title
    st.title("MediWay")
    st.subheader("Blood Report Analysis & Consultation")

    # Sidebar
    with st.sidebar:
        st.header("Menu")

        # Show user info and logout button if authenticated
        if "authenticated" in st.session_state and st.session_state.authenticated:
            st.success(f"Logged in as: {st.session_state.username}")
            if st.button("Logout"):
                if logout():
                    st.rerun()

        st.header("Upload")
        # File uploader (only visible if authenticated)
        if "authenticated" in st.session_state and st.session_state.authenticated:
            uploaded_file = st.file_uploader("Upload Blood Report PDF", type=["pdf"])

        # About section
        st.divider()
        st.markdown("### About MediWay")
        st.info(
            "MediWay helps you understand your blood test results through "
            "AI-powered analysis and personalized insights."
        )

    # Check authentication status
    if "authenticated" not in st.session_state or not st.session_state.authenticated:
        # Show login form if not authenticated
        display_login_form()
    else:
        # Main content area for authenticated users

        # Display patient context form first
        form_submitted = display_patient_form()

        # If form was just submitted, collapse it
        if form_submitted:
            st.session_state.form_collapsed = True

        # Process uploaded file
        if "uploaded_file" in locals() and uploaded_file is not None:
            st.success("File uploaded successfully!")

            # Process the PDF
            with st.spinner("Processing the blood report..."):
                temp_path = save_uploaded_file(uploaded_file)
                success, lab_no = process_pdf(temp_path)

                # Clean up the temp file
                os.unlink(temp_path)

            if success:
                st.success(f"Report processed successfully! Lab Number: {lab_no}")

                # Store the lab number in session state
                st.session_state.current_lab_no = lab_no

                # Get and display report data
                report_data = fetch_report_data(lab_no)
                if report_data:
                    display_report_and_insights(report_data, lab_no)
            else:
                st.error("Failed to process the report. Please try again with a clearer scan.")
        else:
            st.info("Please upload a blood report PDF for analysis.")

            # Sample image
            # col1, col2, col3 = st.columns([1, 3, 1])
            # with col2:
            #    st.image(
            #        "https://www.hopkinsmedicine.org/-/media/images/health/1_-conditions/heart/blood-test-tube-letterbox.jpg",
            #        caption="Upload your blood test report for AI-powered analysis")


if __name__ == "__main__":
    main()