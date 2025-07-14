#!/usr/bin/env python3
"""
Development server script for MediWay
Runs both frontend (Streamlit) and backend (FastAPI) with auto-reload
"""

import subprocess
import sys
import os
import signal
import time
from multiprocessing import Process
import threading

def run_backend():
    """Run the FastAPI backend server"""
    print("🚀 Starting FastAPI backend server...")
    try:
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "backend:app", 
            "--host", "127.0.0.1", 
            "--port", "8080", 
            "--reload"
        ], check=True)
    except KeyboardInterrupt:
        print("\n🛑 Backend server stopped")
    except Exception as e:
        print(f"❌ Backend error: {e}")

def run_frontend():
    """Run the Streamlit frontend server"""
    print("🌐 Starting Streamlit frontend server...")
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            "app.py", 
            "--server.port", "8501",
            "--server.address", "127.0.0.1"
        ], check=True)
    except KeyboardInterrupt:
        print("\n🛑 Frontend server stopped")
    except Exception as e:
        print(f"❌ Frontend error: {e}")

def main():
    """Main function to run both servers"""
    print("🏥 Starting MediWay Development Environment")
    print("=" * 50)
    
    # Check if required files exist
    if not os.path.exists("backend.py"):
        print("❌ backend.py not found!")
        return
    
    if not os.path.exists("app.py"):
        print("❌ app.py not found!")
        return
    
    # Check for .env file
    if not os.path.exists(".env"):
        print("⚠️  .env file not found. Make sure to create one with your API keys!")
    
    print("📋 Starting servers...")
    print("   Backend:  http://127.0.0.1:8080")
    print("   Frontend: http://127.0.0.1:8501")
    print("   API Docs: http://127.0.0.1:8080/docs")
    print("=" * 50)
    print("Press Ctrl+C to stop both servers")
    print()
    
    # Start backend process
    backend_process = Process(target=run_backend)
    backend_process.start()
    
    # Give backend a moment to start
    time.sleep(2)
    
    # Start frontend process
    frontend_process = Process(target=run_frontend)
    frontend_process.start()
    
    try:
        # Wait for both processes
        backend_process.join()
        frontend_process.join()
    except KeyboardInterrupt:
        print("\n🛑 Shutting down servers...")
        backend_process.terminate()
        frontend_process.terminate()
        backend_process.join()
        frontend_process.join()
        print("✅ Servers stopped")

if __name__ == "__main__":
    main() 