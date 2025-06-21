# ui.py

import streamlit as st
import pandas as pd
from utils import fetch_report_data
from chatbot import analyze_report

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
        analysis = analyze_report(report_id, patient_context=st.session_state.get("patient_context", {}))
        if analysis:
            st.session_state[analysis_key] = analysis

    if analysis_key in st.session_state:
        st.markdown(st.session_state[analysis_key])

    st.header("Chat with MediWay")
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "Hello! I'm your medical assistant. You can ask me questions about your blood test results."}
        ]

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Ask about your test results...", key=f"chat_input_{report_id}"):
        st.session_state.messages.append({"role": "user", "content": prompt})
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
                st.session_state.messages.append({"role": "assistant", "content": response})
