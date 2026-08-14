# 📄 Project Structure & File Guide

This document provides a simple, clear description of every single file in the **Python Semantic Cache Chatbot** project.

---

## 🎨 Frontend Files (UI & User Experience)

| File Path | Description in Simple Terms |
| :--- | :--- |
| **`frontend/streamlit_app.py`** | **Main Web App Entrypoint**: Loads custom styling, sets up the page layout, and renders the sidebar and chat window. |
| **`frontend/components/chat_window.py`** | **Chat Interface Screen**: Renders user messages (`👤`) and assistant responses (`🐍`), quick-start question chips, and status badges (**⚡ CACHE HIT** vs **🤖 GEMINI RESPONSE**). |
| **`frontend/components/sidebar.py`** | **Side Navigation Panel**: Displays logo, server connection status, "Clear Chat History" button, and "Reset Cache" button. |
| **`frontend/components/metrics_panel.py`** | **Performance Dashboard**: Displays real-time speed metric cards and response time comparison charts. |
| **`frontend/components/cache_status.py`** | **Cache Inspector Screen**: Provides a search table to view and inspect all question-response pairs currently stored in the FAISS vector database. |
| **`frontend/styles/custom.css`** | **Design & Styling**: Custom CSS that gives the app modern glassmorphism styling, dark background themes, and status badges. |

---

## ⚙️ Backend Files (Server, Logic & Database)

### 1. Main Server & Settings
| File Path | Description in Simple Terms |
| :--- | :--- |
| **`backend/app.py`** | **FastAPI Server Entrypoint**: Initializes the web server, sets up CORS permissions, loads the FAISS index on startup, and exposes API routes. |
| **`backend/config/settings.py`** | **Settings Configuration**: Loads environment variables from `.env` (like API keys, server port, Gemini model name, and default similarity threshold `0.45`). |
| **`backend/config/constants.py`** | **System Prompts & Guardrails**: Contains the system prompt telling Gemini to act as a friendly Python assistant and politely decline non-Python topics. |
| **`backend/__init__.py`** | **Package Marker**: Marks the `backend` directory as a formal Python package. |

---

### 2. Services (Core Brain Logic)
| File Path | Description in Simple Terms |
| :--- | :--- |
| **`backend/services/semantic_cache_service.py`** | **Cache Manager**: Receives a question, searches FAISS vector index, compares similarity score against threshold (`0.45`), and returns cached answer if found. |
| **`backend/services/faiss_service.py`** | **Vector Store Manager**: Handles FAISS index (`faiss.IndexFlatIP`), adds new vectors, performs top-1 similarity searches, and saves index to disk (`faiss.index`). |
| **`backend/services/embedding_service.py`** | **Text-to-Vector Converter**: Converts text questions into 768-dimensional numerical vector representations using Gemini Embedding API (with local fallback). |
| **`backend/services/chatbot_service.py`** | **Google Gemini AI Client**: Communicates with Google Gemini AI API (`gemini-2.0-flash`) using structured multi-turn conversation history to generate responses on cache misses. |
| **`backend/services/metrics_service.py`** | **Speed & Cost Analytics**: Tracks query counts, hit/miss ratios, response latencies (in milliseconds), and saved LLM API calls. |
| **`backend/services/prompt_service.py`** | **Prompt Formatter**: Formats system prompt instructions and multi-turn chat history into a clean prompt string. |

---

### 3. API Routes & Endpoints
| File Path | Description in Simple Terms |
| :--- | :--- |
| **`backend/routes/chat.py`** | **`/api/chat` Route**: Main API endpoint that processes user messages, coordinates cache search, calls Gemini on miss, and returns structured JSON responses. |
| **`backend/routes/cache.py`** | **`/api/cache/*` Routes**: API endpoints to retrieve vector cache statistics, list all cached entries, or clear/reset the cache store. |
| **`backend/routes/metrics.py`** | **`/api/metrics` Routes**: API endpoints to fetch live latency metrics and reset counters. |

---

### 4. Data Models (Schemas)
| File Path | Description in Simple Terms |
| :--- | :--- |
| **`backend/models/chat_models.py`** | **Chat Data Schemas**: Defines Pydantic models for chat requests (`ChatRequest`), messages (`ChatMessage`), and responses (`ChatResponse`). |
| **`backend/models/cache_models.py`** | **Cache Data Schemas**: Defines models for individual cache entries (`CacheEntry`), cache search results (`CacheSearchResult`), and index stats (`CacheStats`). |
| **`backend/models/metrics_models.py`** | **Metrics Data Schemas**: Defines models for system performance KPIs (`SystemMetrics`) and benchmark comparisons. |

---

### 5. Utilities & Helpers
| File Path | Description in Simple Terms |
| :--- | :--- |
| **`backend/utils/similarity.py`** | **Vector Math Helpers**: Utility functions for L2 vector normalization and cosine similarity calculation. |
| **`backend/utils/logger.py`** | **Logging Utility**: Custom formatted logger for printing timestamped log messages to terminal stdout. |
| **`backend/utils/helpers.py`** | **General Helpers**: Utility functions for creating missing directories and generating UTC timestamp strings. |

---

### 6. Automated Unit Tests
| File Path | Description in Simple Terms |
| :--- | :--- |
| **`backend/tests/test_chat.py`** | **Chat API Tests**: Pytest file testing `/api/chat` endpoint, cache hit/miss flow, and off-topic prompt refusal. |
| **`backend/tests/test_cache.py`** | **Cache Unit Tests**: Pytest file testing FAISS vector index additions, similarity lookup, and cache clearing. |
| **`backend/tests/test_embeddings.py`** | **Embedding Tests**: Pytest file testing vector embedding shapes (768-D), normalization, and similarity score calculations. |

---

## 🛠️ Root Project Files

| File Path | Description in Simple Terms |
| :--- | :--- |
| **`benchmark.py`** | **Automated Performance Benchmark**: Script that tests 16 benchmark queries to measure latency reduction, hit rate, and API savings WITH vs WITHOUT cache. |
| **`requirements.txt`** | **Dependency List**: Lists all required Python packages (FastAPI, Streamlit, FAISS, Google GenAI SDK, Pydantic, Pytest). |
| **`README.md`** | **Main Project Overview**: Project documentation with feature breakdown, setup steps, and architecture overview. |
| **`.env.example`** | **Environment Template**: Template file showing how to configure `GEMINI_API_KEY`, `SIMILARITY_THRESHOLD`, and port numbers. |
| **`.gitignore`** | **Git Exclusion Rules**: Tells git to ignore private files like `.env`, virtualenv `venv/`, `__pycache__`, and local `.index` database files. |
