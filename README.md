# MediWay: AI-Powered Medical Report Chatbot

## Overview

MediWay is an innovative medical chatbot application that analyzes patient lab reports and provides personalized, conversational insights. By leveraging advanced AI and natural language processing, MediWay simplifies complex medical information, empowering users to understand their health status with clarity and empathy. The platform bridges the gap between raw medical data and patient comprehension, promoting health literacy and engagement.

---

## Table of Contents

- [Features](#features)
- [How It Works](#how-it-works)
- [System Architecture](#system-architecture)
- [Quick Start](#quick-start)
- [Installation](#installation)
- [Usage](#usage)
- [Development](#development)
- [Evaluation & Benchmarking](#evaluation--benchmarking)
- [File Structure](#file-structure)
- [Contributing](#contributing)
- [License](#license)
- [Acknowledgements](#acknowledgements)

---

## Features

- **Conversational AI**: Empathetic, context-aware chatbot for patient queries.
- **Automated Lab Report Parsing**: Extracts and structures data from uploaded PDF blood reports using OCR and LLMs.
- **Personalized Insights**: Delivers tailored explanations based on patient context (age, gender, symptoms, history, etc.).
- **Secure User Authentication**: User registration, login, and report management.
- **Persistent Chat History**: Stores and retrieves previous conversations for continuity.
- **API-Driven Architecture**: FastAPI backend for scalable, modular deployment.
- **Evaluation Suite**: Tools for benchmarking AI model performance on medical Q&A.

---

## How It Works

1. **User Authentication**: Patients register and log in securely.
2. **Report Upload**: Users upload their blood report PDFs.
3. **Data Extraction**: The first page is converted to an image, OCR is performed, and an LLM parses the text into structured JSON.
4. **Database Storage**: Patient details and test results are stored in MongoDB.
5. **AI Analysis**: The chatbot analyzes the report, considering patient context, and generates a simple, empathetic summary.
6. **Conversational Interface**: Patients can chat with the AI to ask follow-up questions about their results.
7. **Persistence**: All conversations and reports are saved for future reference.

---

## System Architecture

```mermaid
graph TD
    A[User (Web UI)] -->|PDF Upload| B[Streamlit Frontend]
    B -->|API Calls| C[FastAPI Backend]
    C -->|Data| D[MongoDB]
    C -->|LLM API| E[Groq/OpenAI]
    B -->|Chat| C
    C -->|Analysis| E
```

- **Frontend**: Streamlit app for user interaction.
- **Backend**: FastAPI for report processing, chat, and analysis endpoints.
- **Database**: MongoDB for users, reports, tests, and conversations.
- **AI/LLM**: Integrates with Groq/OpenAI for OCR parsing and chat responses.

---

## Quick Start

### 🚀 One-Command Development Setup

**Windows:**
```bash
run_dev.bat
```

**Unix/Linux/macOS:**
```bash
./run_dev.sh
```

**Manual (any platform):**
```bash
python run_dev.py
```

This will start both the frontend and backend servers with auto-reload enabled:
- **Frontend**: http://127.0.0.1:8501
- **Backend**: http://127.0.0.1:8080
- **API Docs**: http://127.0.0.1:8080/docs

---

## Installation

### Prerequisites

- Python 3.8+
- MongoDB (local or cloud)
- Tesseract OCR (for PDF text extraction)
- [Groq/OpenAI API Key](https://groq.com/) (for LLM features)

### Setup

1. **Clone the repository:**
   ```bash
   git clone <repo-url>
   cd mediway
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   - Create a `.env` file with:
     ```
     MONGO_URI=mongodb://localhost:27017
     GROQ_API_KEY=your_groq_api_key
     ```

5. **Run MongoDB** (if not using a cloud instance).

6. **Start development servers:**
   ```bash
   python run_dev.py
   ```

---

## Usage

- **Homepage**: Register or log in.
- **Upload**: Submit your blood report PDF.
- **Review**: View extracted results and AI-generated insights.
- **Chat**: Ask questions about your report in natural language.
- **Manage**: View or delete previous reports and conversations.

---

## Development

### Development Commands

| Command | Description |
|---------|-------------|
| `python run_dev.py` | Start both frontend and backend with auto-reload |
| `run_dev.bat` | Windows batch file for easy startup |
| `./run_dev.sh` | Unix/Linux/macOS script for easy startup |

### Manual Server Startup

If you prefer to run servers separately:

**Backend (FastAPI):**
```bash
uvicorn backend:app --reload --host 127.0.0.1 --port 8080
```

**Frontend (Streamlit):**
```bash
streamlit run app.py --server.port 8501 --server.address 127.0.0.1
```

### Auto-Reload Features

- **Backend**: Uses uvicorn's `--reload` flag to automatically restart on code changes
- **Frontend**: Streamlit automatically reloads on file changes
- **Database**: MongoDB persists data across restarts

---

## Evaluation & Benchmarking

The `evaluation/` directory contains scripts and data for benchmarking LLMs on medical Q&A:

- `model_tester.py`: Runs multiple LLMs on a set of medical questions and stores responses.
- `avg_scores.py`: Computes average similarity scores for model outputs.
- `model_scores.json`/`model_scores_avg.json`: Stores raw and averaged evaluation results.

To run an evaluation:
```bash
cd evaluation
python model_tester.py
python avg_scores.py
```

---

## File Structure

```
mediway/
├── app.py                 # Main Streamlit frontend
├── backend.py             # FastAPI backend for API endpoints
├── chatbot.py             # LLM-based chat and analysis logic
├── preprocessing.py       # PDF/OCR parsing and data extraction
├── auth.py               # User authentication and report management
├── database.py           # MongoDB interactions
├── ui.py                 # UI components for displaying reports and chat
├── utils.py              # Utility functions
├── run_dev.py            # Development server script
├── run_dev.bat           # Windows batch file for easy startup
├── run_dev.sh            # Unix/Linux/macOS script for easy startup
├── requirements.txt      # Python dependencies
├── patent_abstract.txt   # Project abstract and literature review
├── evaluation/           # Model evaluation scripts and data
│   ├── model_tester.py
│   ├── avg_scores.py
│   ├── scoring.py
│   └── *.json files
├── secure/               # Secure deployment variant
├── test/                 # Testing scripts
└── docs/                 # Documentation files
```

---

## Contributing

Contributions are welcome! Please open issues or pull requests for bug fixes, features, or documentation improvements.

### Development Workflow

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test with `python run_dev.py`
5. Submit a pull request

---

## License

[MIT License](LICENSE) (or specify your license here)

---

## Acknowledgements

- Inspired by research on AI in healthcare and conversational agents.
- Uses open-source libraries: Streamlit, FastAPI, MongoDB, Tesseract, and Groq/OpenAI APIs.

---

**For more details, see the `patent_abstract.txt` and `docs/` directory.** 