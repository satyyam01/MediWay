# utils.py

import tempfile
import os
import requests
import streamlit as st

API_BASE_URL = "http://127.0.0.1:8080"  # or your FastAPI URL

def save_uploaded_file(uploaded_file):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(uploaded_file.getvalue())
        return tmp.name

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
