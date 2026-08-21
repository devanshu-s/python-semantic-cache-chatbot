# 🐍 Python Assistant & Semantic Cache — Project Brief

- **What the code is about**: A full-stack AI Python coding assistant and live sandbox compiler accelerated by a high-performance vector semantic cache.
- **What this chatbot is**: A conversational Python mentor powered by Google Gemini that answers programming queries using a Test-Driven Development (TDD) approach.
- **What FAISS is**: Facebook AI Similarity Search (FAISS) is an ultra-fast vector search library used here to compare 768-dimensional query embeddings using Cosine Similarity (Inner Product).
- **What the frontend is**: A Streamlit interactive web application (`frontend/streamlit_app.py`) providing a split-screen UI for chat conversation and a live Python code compiler sandbox.
- **What the backend is**: A FastAPI REST API server (`backend/app.py`) managing semantic cache lookups, Gemini LLM invocations, FAISS vector indexing, and test case execution endpoints.
- **Where the guardrails are stored**: In `backend/config/constants.py` under `PYTHON_GUARDRAIL_SYSTEM_PROMPT`, strictly restricting responses to Python programming and enforcing the Test-First structure.
- **How code generation works**: When a problem is asked, Gemini first presents the **Top 10 Test Cases & Edge Cases Analysis**, then generates the optimal Python code designed specifically to pass all 10 cases.
- **How moving code to compiler and vice versa works**: "Copy to Code Box" loads both the code and the 10 test cases directly into the IDE sandbox for execution, while "Send to Chatbot" transfers failed cases and user comments back to chat for iterative fixing.
- **How Gemini calculates edge cases**: Gemini identifies standard cases, empty inputs, zero/negatives, single elements, boundaries, duplicates, and scale constraints for the problem before writing any code.
- **Where and how queries are stored**: When a query results in a cache miss, its vector embedding is saved into `backend/database/faiss.index` and its text Q&A metadata is saved into `backend/database/cache_store.json`.
- **What the threshold is, how it is chosen, and what is best**: The threshold is the minimum cosine similarity (0.0–1.0) needed for a Cache Hit; lower values allow looser matches while higher values require exact matches, with **`0.60` – `0.70` being the optimal sweet spot** for high hit rates without false matches.
