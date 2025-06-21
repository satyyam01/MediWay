import streamlit as st
import os
import tempfile
import requests
import pandas as pd
from pymongo import MongoClient
from dotenv import load_dotenv

from preprocessing import MedicalReportProcessor
from utils import save_uploaded_file
from auth import show_my_reports
from database import get_conversation_history, update_conversation_history
from chatbot import analyze_report

# Load environment variables
load_dotenv()

# MongoDB setup
client = MongoClient(os.getenv("MONGO_URI", "mongodb://localhost:27017"))
db = client["mediway"]
patients_collection = db["patients"]
tests_collection = db["tests"]

API_BASE_URL = "http://127.0.0.1:8080"  # FastAPI base URL


@st.cache_data(show_spinner=False)
def fetch_report_data(report_id):
    try:
        response = requests.get(f"{API_BASE_URL}/report/{report_id}")
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error fetching report: {response.text}")
            return None
    except Exception as e:
        st.error(f"API connection error: {e}")
        return None


def get_analysis(report_id):
    try:
        with st.spinner("Analyzing report with AI..."):
            response = requests.post(
                f"{API_BASE_URL}/analyze/{report_id}",
                json={"patient_context": st.session_state.get("patient_context", {})}
            )
            if response.status_code == 200:
                return response.json()["analysis"]
            else:
                st.error(f"Error getting analysis: {response.text}")
                return None
    except Exception as e:
        st.error(f"AI analysis error: {e}")
        return None


def display_report_and_insights(report_data, report_id):
    st.header("Patient Information")
    patient = report_data["Patient Details"]

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**Name:** {patient['Name']}")
        st.markdown(f"**Age:** {patient['Age']}")
        st.markdown(f"**Gender:** {patient['Gender']}")
    with col2:
        st.markdown(f"**Sample Collected:** {patient['Collected Date']}")
        st.markdown(f"**Report Date:** {patient['Reported Date']}")
        st.markdown(f"**Report ID:** `{report_id}`")

    st.header("Test Results")
    test_data = [
        {
            "Test Name": test["Name"],
            "Result": test["Value"],
            "Unit": test["Unit"],
            "Reference Range": test["Reference Interval"]
        } for test in report_data["Tests"]
    ]
    df = pd.DataFrame(test_data)
    st.dataframe(df, use_container_width=True)

    st.header("AI Analysis")
    analysis_key = f"analysis_{report_id}"
    if analysis_key not in st.session_state:
        analysis = get_analysis(report_id)
        if analysis:
            st.session_state[analysis_key] = analysis

    if analysis_key in st.session_state:
        st.markdown(st.session_state[analysis_key])

    st.header("Chat with MediWay")

    # Step 1: Load and display previous conversation from DB
    history = get_conversation_history(report_id)

    for msg in history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Step 2: Handle new input
    if prompt := st.chat_input("Ask about your test results...", key=f"chat_input_{report_id}"):
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = analyze_report(
                    report_id,
                    custom_prompt=prompt,
                    patient_context=st.session_state.get("patient_context", {})
                )
                st.markdown(response)

        # Step 3: Save to MongoDB for persistence
        update_conversation_history(report_id, prompt, response)


def app_dashboard():
    st.title(f"Welcome to MediWay, {st.session_state.get('username', 'User')} \U0001F44B")

    # Sidebar - Patient Context
    with st.sidebar:
        st.header("\U0001FA7A Patient Context")
        context = st.session_state.get("patient_context", {})
        with st.form("patient_context_form"):
            name = st.text_input("Name", value=context.get("name", ""), key="context_name")
            age = st.number_input("Age", min_value=0, max_value=120, step=1, value=context.get("age", 0), key="context_age")
            gender = st.selectbox("Gender", ["Male", "Female", "Other"], index=["Male", "Female", "Other"].index(context.get("gender", "Male")), key="context_gender")
            weight = st.number_input("Weight (kg)", min_value=0.0, max_value=300.0, step=0.1, value=context.get("weight", 0.0), key="context_weight")
            height = st.number_input("Height (cm)", min_value=0.0, max_value=250.0, step=0.1, value=context.get("height", 0.0), key="context_height")
            symptoms = st.text_area("Symptoms (comma separated)", value=", ".join(context.get("symptoms", [])), key="context_symptoms")
            history = st.text_area("Past Medical History", value=context.get("history", ""), key="context_history")

            submitted = st.form_submit_button("Save Context")
            if submitted:
                st.session_state.patient_context = {
                    "name": name,
                    "age": age,
                    "gender": gender,
                    "weight": weight,
                    "height": height,
                    "symptoms": [s.strip() for s in symptoms.split(",") if s.strip()],
                    "history": history
                }
                st.success("Patient context saved!")

        st.header("\U0001F4E4 Upload Report")
        uploaded_file = st.file_uploader("Upload Blood Report PDF", type=["pdf"])

        st.divider()
        if st.button("\U0001F6AA Logout", use_container_width=True):
            st.session_state.clear()
            st.rerun()

        st.divider()
        st.markdown("### ℹ️ About MediWay")
        st.info("MediWay helps you understand your blood test results through AI-powered analysis and personalized insights.")

    # Show User Reports
    show_my_reports()

    # Handle New Upload
    if uploaded_file is None:
        st.session_state.upload_handled = False

    if uploaded_file is not None and not st.session_state.get("upload_handled", False):
        st.session_state.upload_handled = True
        st.success("File uploaded successfully!")

        with st.spinner("\U0001F50D Processing the blood report..."):
            temp_path = save_uploaded_file(uploaded_file)
            processor = MedicalReportProcessor(username=st.session_state.get("username"))
            ctx = st.session_state.get("patient_context", {})
            report_id = processor.process_report(temp_path, name=ctx.get("name", ""), age=ctx.get("age", 0), gender=ctx.get("gender", ""))
            os.unlink(temp_path)

        if report_id:
            st.session_state.pop(f"analysis_{report_id}", None)
            st.session_state.pop(f"messages_{report_id}", None)
            st.session_state.current_report_id = report_id
            st.success(f"✅ Report processed! Report ID: `{report_id}`")
            st.rerun()
        else:
            st.error("❌ Failed to process the report. Try uploading a clearer scan.")

    report_id = st.session_state.get("current_report_id")
    if report_id:
        report_data = fetch_report_data(report_id)
        if report_data:
            display_report_and_insights(report_data, report_id)
        else:
            st.error("Report data not found. Please try again.")


def main():
    st.set_page_config(page_title="MediWay - Blood Report Analysis", page_icon="\U0001FA78", layout="wide")

    if "page" not in st.session_state:
        st.session_state.page = "login"

    if st.session_state.page == "login":
        from auth import login_page
        login_page()

    elif st.session_state.page == "signup":
        from auth import signup_page
        signup_page()

    elif st.session_state.page == "dashboard":
        if st.session_state.get("logged_in"):
            app_dashboard()
        else:
            st.session_state.page = "login"
            st.rerun()


if __name__ == "__main__":
    main()