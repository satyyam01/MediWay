import streamlit as st
from auth import homepage, login_page, signup_page
from app import main as app_main  # Your existing medical report app

def main():
    """Main application flow"""
    # Initialize session state variables if not exist
    if 'page' not in st.session_state:
        st.session_state.page = 'home'

    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False

    # Routing based on session state
    if st.session_state.logged_in:
        # Call the existing medical report app main function
        app_main()
    else:
        # Routing for authentication pages
        if st.session_state.page == 'home':
            homepage()
        elif st.session_state.page == 'login':
            login_page()
        elif st.session_state.page == 'signup':
            signup_page()

if __name__ == "__main__":
    main()