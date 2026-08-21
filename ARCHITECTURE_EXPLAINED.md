# 🐍 Semantic Cache Chatbot - Architecture & Concepts Guide

This guide provides a comprehensive breakdown of the tech stack, components, guardrails, threshold settings, and preloaded cache system.

---

## 1. ⚡ What is FAISS?

**FAISS** (*Facebook AI Similarity Search*) is an open-source vector search library developed by Meta AI.

- **Role in this project**: It acts as the high-speed **vector engine** for the semantic cache.
- **Implementation**: Located in [`backend/services/faiss_service.py`](file:///Users/devanshusharma/Desktop/SEMANTIC%20CHATBOT/backend/services/faiss_service.py).
- **Index Type**: `faiss.IndexFlatIP` (Inner Product). Because embeddings are normalized to unit length, Inner Product is mathematically identical to **Cosine Similarity**.
- **Vector Dimension**: 768-dimensional float32 vectors.
- **Speed**: Performs vector similarity search in **< 1 millisecond**.

---

## 2. 🎨 How is the Frontend Made?

The frontend is built using **Streamlit**, a Python framework for creating web applications.

- **Main Entrypoint**: [`frontend/streamlit_app.py`](file:///Users/devanshusharma/Desktop/SEMANTIC%20CHATBOT/frontend/streamlit_app.py)
- **Modular Component Breakdown**:
  1. **Sidebar Controls** ([`frontend/components/sidebar.py`](file:///Users/devanshusharma/Desktop/SEMANTIC%20CHATBOT/frontend/components/sidebar.py)):
     - Interactive **Similarity Threshold Slider Bar** (`0.00` to `1.00`).
     - **Export Chat History** button (downloads Markdown format `.md`).
     - **Clear Chat** and **Reset Cache** actions.
     - Live backend connectivity indicator.
  2. **Chat Window** ([`frontend/components/chat_window.py`](file:///Users/devanshusharma/Desktop/SEMANTIC%20CHATBOT/frontend/components/chat_window.py)):
     - Conversational chat history UI with custom user 👤 and assistant 🐍 avatars.
     - **⚡ CACHE HIT** vs **🤖 GEMINI RESPONSE** status badges with response latency.
     - Quick suggestion chips & topic-aware follow-up question buttons.
     - **📋 Copy to Code Box** button.
  3. **Python Code Sandbox** ([`frontend/components/code_sandbox.py`](file:///Users/devanshusharma/Desktop/SEMANTIC%20CHATBOT/frontend/components/code_sandbox.py)):
     - Interactive code editor & runner for executing Python snippets directly in the browser.
  4. **Metrics Telemetry Panel** ([`frontend/components/metrics_panel.py`](file:///Users/devanshusharma/Desktop/SEMANTIC%20CHATBOT/frontend/components/metrics_panel.py)):
     - Displays cache hit ratio (%), total saved API calls, and average latency comparisons.

---

## 3. ⚙️ How is the Backend Made?

The backend is built with **FastAPI** and served using **Uvicorn** (ASGI server).

- **Main Server Entrypoint**: [`backend/app.py`](file:///Users/devanshusharma/Desktop/SEMANTIC%20CHATBOT/backend/app.py)
- **API Routes**:
  - [`backend/routes/chat.py`](file:///Users/devanshusharma/Desktop/SEMANTIC%20CHATBOT/backend/routes/chat.py): `POST /api/chat` (processes queries, checks cache, calls Gemini API on miss, stores responses).
  - [`backend/routes/cache.py`](file:///Users/devanshusharma/Desktop/SEMANTIC%20CHATBOT/backend/routes/cache.py): `GET /api/cache/stats`, `POST /api/cache/clear`, `GET/POST /api/cache/threshold`.
  - [`backend/routes/metrics.py`](file:///Users/devanshusharma/Desktop/SEMANTIC%20CHATBOT/backend/routes/metrics.py): `GET /api/metrics`.
- **Services Architecture**:
  - `semantic_cache_service.py`: Orchestrates cache search, storage, and thresholding.
  - `embedding_service.py`: Generates 768-dim normalized embeddings using Gemini API (with deterministic fallback).
  - `chatbot_service.py`: Connects to Google Gemini API (`gemini-2.0-flash` / `gemini-3.1-flash-lite`).
  - `faiss_service.py`: Manages the FAISS vector index on disk.
  - `metrics_service.py`: Tracks hit counts, miss counts, and latency statistics.

---

## 4. 🛡️ Where are Guardrails Stored?

System guardrails ensure that the chatbot responds **only to Python programming queries**.

- **Prompt Definition**: Defined in [`backend/config/constants.py`](file:///Users/devanshusharma/Desktop/SEMANTIC%20CHATBOT/backend/config/constants.py) as `PYTHON_GUARDRAIL_SYSTEM_PROMPT`.
- **Enforcement**: Applied in [`backend/services/chatbot_service.py`](file:///Users/devanshusharma/Desktop/SEMANTIC%20CHATBOT/backend/services/chatbot_service.py) via `system_instruction` in Google Gemini API calls.
- **Behavior**: If a user asks non-Python questions (e.g. recipes, non-coding history, general trivia), the chatbot politely refuses:
  > *"I am specialized strictly as a Python programming assistant. I'd be happy to help you with any Python code, library, or programming question!"*

---

## 5. 🎛️ What is Threshold?

The **Similarity Threshold** (`SIMILARITY_THRESHOLD`) is the minimum cosine similarity score (between `0.00` and `1.00`) required for a vector match in FAISS to count as a **⚡ CACHE HIT**.

- **Formula**: $\text{Cosine Similarity} = \frac{\vec{A} \cdot \vec{B}}{\|\vec{A}\| \|\vec{B}\|}$
- **Default Value**: `0.60` (defined in [.env](file:///Users/devanshusharma/Desktop/SEMANTIC%20CHATBOT/.env)).
- **Adjuster Slider**: Users can adjust the threshold dynamically in the Streamlit sidebar:
  - 🎯 **Strict Mode (< 0.40)**: Requires higher precision, resulting in fewer cache hits.
  - ⚖️ **Balanced Mode (0.40 - 0.70)**: Optimal balance between cache hit rate and query relevance.
  - ⚡ **High Cache Hits (> 0.70)**: Accepts looser semantic matches to maximize cached responses.

---

## 6. 📁 Where are Preloaded Cache Files Stored?

The preloaded cache consists of **151 Q&A pairs** covering Python syntax, data structures, OOP, ML, and LLM concepts.

1. **JSON Metadata File**: [`backend/database/cache_store.json`](file:///Users/devanshusharma/Desktop/SEMANTIC%20CHATBOT/backend/database/cache_store.json)
   - Contains the 151 question-response dictionary entries, timestamps, and assigned vector IDs.
2. **FAISS Vector Index File**: `backend/database/faiss.index`
   - Binary vector index containing the 151 normalized float32 embeddings.
3. **Seeding Script**: [`scripts/seed_cache.py`](file:///Users/devanshusharma/Desktop/SEMANTIC%20CHATBOT/scripts/seed_cache.py)
   - Utility script used to iterate over `cache_store.json` and generate/rebuild `faiss.index`.

---

## 🚀 Quick Run Summary

To launch the backend and frontend:

```bash
# 1. Activate environment
source venv/bin/activate

# 2. Start Backend API
PYTHONPATH=. uvicorn backend.app:app --port 8000 --reload

# 3. Start Frontend UI (in a new tab)
streamlit run frontend/streamlit_app.py
```
