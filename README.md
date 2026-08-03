# Python Programming Chatbot with Semantic Cache

Hi! 👋 This is my project for a Python programming assistant chatbot. It uses **Google Gemini** for generating answers, **FastAPI** for the backend, **Streamlit** for the frontend UI, and **FAISS** for semantic caching to save API calls and get faster responses for similar questions.

---

## 📌 Project Overview

When asking Python coding questions, many queries are semantically similar (for example: *"How to reverse a list in Python?"* vs *"Python list reversal example"*). 

Instead of calling the Gemini API every single time, this project converts questions into vector embeddings and searches a **FAISS** vector store. If a similar question has been asked before, it returns the cached response in less than a millisecond!

---

## 🧰 Tech Stack

- **Frontend**: Streamlit
- **Backend**: FastAPI, Uvicorn
- **AI / LLM**: Google Gemini API (`gemini-2.0-flash`)
- **Vector Search**: FAISS
- **Language**: Python 3.10+

---

## 📁 Project Structure

```text
semantic-cache-chatbot/
│
├── backend/
│   ├── app.py                      # Main FastAPI server
│   ├── config/                     # Settings and environment variables
│   ├── models/                     # Pydantic data schemas
│   ├── routes/                     # Chat and cache API routes
│   ├── services/                   # FAISS cache, Gemini API, and embedding logic
│   ├── database/                   # FAISS index and cache JSON file
│   └── tests/                      # Pytest test cases
│
├── frontend/
│   ├── streamlit_app.py            # Streamlit main app
│   ├── components/                 # Chat window and sidebar UI
│   └── styles/                     # Custom CSS styles
│
├── benchmark.py                    # Benchmark script to test cache performance
├── requirements.txt                # Project dependencies
├── README.md                       # Project documentation
└── .env.example                    # Example environment setup file
```

---

## ⚙️ How to Run Locally

### 1. Clone the repository and setup environment

```bash
git clone <repo-url>
cd semantic-cache-chatbot

python3 -m venv venv
source venv/bin/activate
```

### 2. Install requirements

```bash
pip install -r requirements.txt
```

### 3. Create `.env` file

Copy `.env.example` to `.env` and add your Gemini API key:

```env
GEMINI_API_KEY=your_gemini_api_key_here
SIMILARITY_THRESHOLD=0.45
GEMINI_MODEL=gemini-2.0-flash
```

### 4. Start the Backend API

```bash
PYTHONPATH=. uvicorn backend.app:app --port 8000 --reload
```

Backend API will run at `http://localhost:8000`.

### 5. Start the Streamlit Frontend

In a new terminal tab (with virtualenv activated):

```bash
streamlit run frontend/streamlit_app.py
```

Frontend app will open at `http://localhost:8501`.

---

## 🧪 Running Tests & Benchmark

To run unit tests:
```bash
PYTHONPATH=. pytest backend/tests/ -v
```

To run the benchmark script comparing latency with vs without cache:
```bash
PYTHONPATH=. python benchmark.py
```

---

## 📝 Features & Notes

- Answers only Python programming questions.
- Remembers multi-turn chat history during a session.
- Automatically saves new Q&A pairs to FAISS vector index.
- Show badges for **⚡ CACHE HIT** vs **🤖 GEMINI RESPONSE**.
