@echo off
echo 🏥 Starting MediWay Development Environment
echo ==================================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found! Please install Python and try again.
    pause
    exit /b 1
)

REM Check if virtual environment exists and activate it
if exist "venv\Scripts\activate.bat" (
    echo 📦 Activating virtual environment...
    call venv\Scripts\activate.bat
) else if exist ".venv\Scripts\activate.bat" (
    echo 📦 Activating virtual environment...
    call .venv\Scripts\activate.bat
) else (
    echo ⚠️  No virtual environment found. Running with system Python.
)

REM Run the development script
echo 🚀 Starting servers...
python run_dev.py

pause 