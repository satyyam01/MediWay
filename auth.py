import streamlit as st
import bcrypt
import sqlite3
import re
from functools import wraps


class StreamlitAuth:
    def __init__(self, db_path="auth.db"):
        self.db_path = db_path
        self._setup_database()

    def _setup_database(self):
        """Initialize the authentication database if it doesn't exist"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create users table if it doesn't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        conn.commit()
        conn.close()

    def _hash_password(self, password):
        """Hash a password using bcrypt"""
        password_bytes = password.encode('utf-8')
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password_bytes, salt)
        return hashed.decode('utf-8')

    def _verify_password(self, password, hashed_password):
        """Verify a password against its hash"""
        password_bytes = password.encode('utf-8')
        hashed_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hashed_bytes)

    def _validate_email(self, email):
        """Validate email format"""
        pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        return re.match(pattern, email) is not None

    def _validate_username(self, username):
        """Validate username (alphanumeric, 3-20 chars)"""
        pattern = r'^[a-zA-Z0-9_]{3,20}$'
        return re.match(pattern, username) is not None

    def _validate_password(self, password):
        """Validate password strength (min 8 chars)"""
        return len(password) >= 8

    def register_user(self, username, email, password):
        """Register a new user"""
        # Validate inputs
        if not self._validate_username(username):
            return False, "Username must be 3-20 characters and contain only letters, numbers, and underscores"

        if not self._validate_email(email):
            return False, "Please enter a valid email address"

        if not self._validate_password(password):
            return False, "Password must be at least 8 characters long"

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Check if username or email already exists
            cursor.execute("SELECT * FROM users WHERE username = ? OR email = ?", (username, email))
            if cursor.fetchone():
                conn.close()
                return False, "Username or email already exists"

            # Hash password and store user
            hashed_password = self._hash_password(password)
            cursor.execute(
                "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
                (username, email, hashed_password)
            )

            conn.commit()
            conn.close()
            return True, "Registration successful"

        except Exception as e:
            return False, f"Registration error: {str(e)}"

    def authenticate(self, username_or_email, password):
        """Authenticate a user by username/email and password"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Check if input is email or username
            is_email = '@' in username_or_email

            if is_email:
                cursor.execute("SELECT username, password_hash FROM users WHERE email = ?", (username_or_email,))
            else:
                cursor.execute("SELECT username, password_hash FROM users WHERE username = ?", (username_or_email,))

            user = cursor.fetchone()
            conn.close()

            if not user:
                return False, "User not found"

            username, stored_hash = user

            if self._verify_password(password, stored_hash):
                return True, username
            else:
                return False, "Incorrect password"

        except Exception as e:
            return False, f"Authentication error: {str(e)}"


def login_required(func):
    """Decorator to require login for a Streamlit page"""

    @wraps(func)
    def wrapper(*args, **kwargs):
        if "authenticated" not in st.session_state or not st.session_state.authenticated:
            st.warning("Please log in to access this page")
            display_login_form()
            return None
        return func(*args, **kwargs)

    return wrapper


def display_login_form():
    """Display the login form"""
    auth = StreamlitAuth()

    # Initialize session state for authentication
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
        st.session_state.username = None

    st.header("Login")

    # Login tab
    login_tab, register_tab = st.tabs(["Login", "Register"])

    with login_tab:
        with st.form("login_form"):
            username_or_email = st.text_input("Username or Email")
            password = st.text_input("Password", type="password")
            login_button = st.form_submit_button("Login")

            if login_button and username_or_email and password:
                success, result = auth.authenticate(username_or_email, password)
                if success:
                    st.session_state.authenticated = True
                    st.session_state.username = result
                    st.success(f"Welcome back, {result}!")
                    st.rerun()
                else:
                    st.error(result)

    with register_tab:
        with st.form("register_form"):
            new_username = st.text_input("Username (letters, numbers, underscores)")
            new_email = st.text_input("Email")
            new_password = st.text_input("Password (min 8 characters)", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            register_button = st.form_submit_button("Register")

            if register_button:
                if not new_username or not new_email or not new_password:
                    st.error("Please fill in all fields")
                elif new_password != confirm_password:
                    st.error("Passwords do not match")
                else:
                    success, message = auth.register_user(new_username, new_email, new_password)
                    if success:
                        st.success(message)
                        st.info("You can now log in with your credentials")
                    else:
                        st.error(message)


def logout():
    """Log out the current user"""
    if "authenticated" in st.session_state:
        st.session_state.authenticated = False
        st.session_state.username = None
        return True
    return False