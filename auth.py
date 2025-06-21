import streamlit as st
import bcrypt
import re
from pymongo import MongoClient
from datetime import datetime
import os
from dotenv import load_dotenv
from database import delete_report_and_related_data  # Make sure this is at the top


# --- Load Environment Variables ---
load_dotenv()
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")

# --- MongoDB Connection ---
client = MongoClient(MONGO_URI)
db = client["mediway"]
users_col = db["users"]
patients_col = db["patients"]

# --- Validators ---
def validate_email(email: str) -> bool:
    return re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email) is not None

def validate_password(password: str) -> bool:
    return (
        len(password) >= 8 and
        any(c.isupper() for c in password) and
        any(c.islower() for c in password) and
        any(c.isdigit() for c in password)
    )

# --- User Registration ---
def register_user(username: str, email: str, password: str):
    if users_col.find_one({"username": username}):
        return False, "❌ Username already exists."

    if users_col.find_one({"email": email}):
        return False, "❌ Email is already registered."

    hashed_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt())

    users_col.insert_one({
        "username": username,
        "email": email,
        "password": hashed_pw,
        "reports": [],
        "created_at": datetime.utcnow()
    })

    return True, "✅ Account created successfully!"

# --- User Login ---
def login_user(username: str, password: str):
    user = users_col.find_one({"username": username})
    if user and bcrypt.checkpw(password.encode(), user["password"]):
        return True, user
    return False, None

# --- Login Page ---
def login_page():
    st.title("🔐 Login to MediWay")

    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")

        if submitted:
            if not username or not password:
                st.error("⚠️ All fields are required.")
            else:
                success, user = login_user(username, password)
                if success:
                    st.session_state.logged_in = True
                    st.session_state.username = user["username"]
                    st.session_state.page = "dashboard"
                    st.session_state.user = {
                        "username": user["username"],
                        "email": user["email"],
                        "_id": str(user["_id"])
                    }
                    st.rerun()
                else:
                    st.error("❌ Invalid username or password.")

    st.divider()
    if st.button("Don't have an account? 👉 Sign Up"):
        st.session_state.page = "signup"
        st.rerun()

# --- Signup Page ---
def signup_page():
    st.title("📝 Create Your MediWay Account")

    with st.form("signup_form"):
        username = st.text_input("Username")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")
        submitted = st.form_submit_button("Sign Up")

        if submitted:
            if not all([username, email, password, confirm_password]):
                st.error("⚠️ Please fill out all fields.")
            elif password != confirm_password:
                st.error("❌ Passwords do not match.")
            elif not validate_email(email):
                st.error("❌ Invalid email format.")
            elif not validate_password(password):
                st.warning("⚠️ Password must be 8+ characters long, and include uppercase, lowercase, and digits.")
            else:
                success, msg = register_user(username, email, password)
                if success:
                    st.success(msg)
                    st.session_state.page = "login"
                    st.rerun()
                else:
                    st.error(msg)

    st.divider()
    if st.button("Already have an account? 👉 Login"):
        st.session_state.page = "login"
        st.rerun()

# --- Report Viewer (My Reports) ---

def show_my_reports():
    st.markdown("## 📄 My Uploaded Reports")

    username = st.session_state.get("username")
    if not username:
        st.warning("⚠️ Please login to view your uploaded reports.")
        return

    reports = list(patients_col.find({"username": username}).sort("reported_date", -1))

    if not reports:
        st.info("📝 You haven’t uploaded any reports yet.")
        return

    for i, report in enumerate(reports):
        report_id = report.get("report_id")
        with st.expander(f"{report.get('name', 'Unknown')} | {report.get('reported_date', 'Date N/A')}"):
            st.markdown(f"**Patient Name:** {report.get('name', '')}")
            st.markdown(f"**Age:** {report.get('age', '')}")
            st.markdown(f"**Gender:** {report.get('gender', '')}")
            st.markdown(f"**Reported On:** {report.get('reported_date', '')}")
            st.markdown(f"**Report ID:** `{report_id}`")

            col1, col2 = st.columns([3, 1])
            with col1:
                if st.button("📊 View Report", key=f"view_{report_id}"):
                    st.session_state.current_report_id = report_id
                    st.session_state.page = "dashboard"
                    st.rerun()

            with col2:
                if st.button("🗑️ Delete", key=f"delete_{report_id}"):
                    success = delete_report_and_related_data(report_id)

                    # Clean session state
                    st.session_state.pop(f"analysis_{report_id}", None)
                    st.session_state.pop(f"messages_{report_id}", None)

                    if st.session_state.get("current_report_id") == report_id:
                        st.session_state.current_report_id = None

                    if success:
                        st.success(f"✅ Report `{report_id}` deleted.")
                    else:
                        st.error(f"❌ Failed to delete report `{report_id}`.")
                    st.rerun()
