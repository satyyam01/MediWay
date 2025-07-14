#!/bin/bash

echo "🏥 Starting MediWay Development Environment"
echo "=================================================="
echo

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not found! Please install Python and try again."
    exit 1
fi

# Check if virtual environment exists and activate it
if [ -d "venv" ]; then
    echo "📦 Activating virtual environment..."
    source venv/bin/activate
elif [ -d ".venv" ]; then
    echo "📦 Activating virtual environment..."
    source .venv/bin/activate
else
    echo "⚠️  No virtual environment found. Running with system Python."
fi

# Make the script executable
chmod +x run_dev.py

# Run the development script
echo "🚀 Starting servers..."
python3 run_dev.py 