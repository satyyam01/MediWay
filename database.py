from pymongo import MongoClient
import bcrypt
from typing import Dict, List
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")

# Reusable MongoDB connection
mongo_client = MongoClient(MONGO_URI)
db = mongo_client["mediway"]
users_collection = db["users"]
patients_collection = db["patients"]
tests_collection = db["tests"]
conversations_collection = db["conversations"]

# In-memory conversation cache
conversation_cache: Dict[str, List[Dict[str, str]]] = {}


# -----------------------------------
# User Authentication
# -----------------------------------

class UserDatabase:
    def __init__(self):
        # Ensure index
        users_collection.create_index("username", unique=True)

    def user_exists(self, username: str) -> bool:
        return users_collection.find_one({"username": username}) is not None

    def register_user(self, username: str, password: str, email: str) -> bool:
        if self.user_exists(username):
            return False
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        try:
            users_collection.insert_one({
                "username": username,
                "password": hashed_password,
                "email": email
            })
            return True
        except Exception as e:
            print("Registration error:", e)
            return False

    def login_user(self, username: str, password: str) -> bool:
        user = users_collection.find_one({"username": username})
        if user and bcrypt.checkpw(password.encode('utf-8'), user["password"]):
            return True
        return False


# -----------------------------------
# Fetching Patient + Test Data
# -----------------------------------

def fetch_patient_data(report_id: str) -> Dict:
    try:
        patient = patients_collection.find_one({"report_id": report_id})
        if not patient:
            return None

        tests = list(tests_collection.find({"report_id": report_id}))

        return {
            "Patient Details": {
                "Name": patient.get("name"),
                "Age": patient.get("age"),
                "Gender": patient.get("gender"),
                "Collected Date": patient.get("collected_date"),
                "Reported Date": patient.get("reported_date")
            },
            "Tests": [
                {
                    "Name": test["test_name"],
                    "Value": test["result"],
                    "Unit": test["unit"],
                    "Reference Interval": test.get("reference_interval", "")
                }
                for test in tests
            ]
        }
    except Exception as e:
        print("Error fetching patient data:", e)
        return None


# -----------------------------------
# Conversation Management
# -----------------------------------

def get_conversation_history(report_id: str) -> List[Dict[str, str]]:
    if report_id not in conversation_cache:
        conversation_cache[report_id] = _load_conversation_from_db(report_id)
    return conversation_cache[report_id]


def update_conversation_history(report_id: str, user_message: str, bot_response: str) -> None:
    history = get_conversation_history(report_id)
    history.append({"role": "user", "content": user_message})
    history.append({"role": "assistant", "content": bot_response})

    # Keep only last 10 entries
    conversation_cache[report_id] = history[-10:]
    _save_conversation_to_db(report_id, conversation_cache[report_id])


def clear_conversation_history(report_id: str) -> None:
    if report_id in conversation_cache:
        del conversation_cache[report_id]
    conversations_collection.delete_one({"report_id": report_id})


def _save_conversation_to_db(report_id: str, conversation_data: List[Dict[str, str]]) -> None:
    try:
        conversations_collection.update_one(
            {"report_id": report_id},
            {
                "$set": {
                    "conversation_data": conversation_data,
                    "last_updated": datetime.utcnow()
                }
            },
            upsert=True
        )
    except Exception as e:
        print("Error saving conversation:", e)


def _load_conversation_from_db(report_id: str) -> List[Dict[str, str]]:
    try:
        doc = conversations_collection.find_one({"report_id": report_id})
        if doc:
            return doc.get("conversation_data", [])
    except Exception as e:
        print("Error loading conversation:", e)
    return []

def delete_report_and_related_data(report_id: str) -> bool:
    try:
        # Delete patient record
        patients_collection.delete_one({"report_id": report_id})

        # Delete related test results
        tests_collection.delete_many({"report_id": report_id})

        # Delete conversation history from cache and DB
        clear_conversation_history(report_id)

        # Optional: Remove from user's report list if tracking (not used currently)
        users_collection.update_many({}, {"$pull": {"reports": report_id}})

        print(f"✅ Deleted report and related data for report_id: {report_id}")
        return True
    except Exception as e:
        print(f"❌ Error deleting report data for {report_id}: {e}")
        return False

