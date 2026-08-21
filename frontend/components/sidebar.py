import os
import streamlit as st
import requests
from datetime import datetime


def generate_markdown_export() -> str:
    """
    Format session chat history into a downloadable markdown report.
    """
    history = st.session_state.get("chat_history", [])
    if not history:
        return "# 🐍 Python Assistant - Chat Export\n\n*No chat messages recorded yet.*"

    md_lines = [
        "# 🐍 Python Assistant - Chat Export History",
        f"*Exported on {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}*\n",
        "---",
        ""
    ]

    for idx, msg in enumerate(history, 1):
        role = "User" if msg["role"] == "user" else "Assistant"
        md_lines.append(f"### Turn {idx} ({role})")
        md_lines.append(msg["content"])
        
        if role == "Assistant" and "metadata" in msg:
            meta = msg["metadata"]
            source = "⚡ CACHE HIT" if meta.get("is_cached") else "🤖 GEMINI API"
            latency = meta.get("total_latency_ms", 0.0)
            score = meta.get("similarity_score", 0.0)
            md_lines.append(f"\n*> [{source}] Latency: {latency:.1f}ms | Similarity Score: {score*100:.1f}%*\n")
        
        md_lines.append("\n---\n")

    return "\n".join(md_lines)


def render_sidebar(backend_url: str):
    """
    Render a clean Streamlit sidebar for user auth, ChatGPT-style chat sessions,
    chat controls, chat export, and backend health status.
    """
    with st.sidebar:
        st.image("https://img.icons8.com/color/96/python--v1.png", width=56)
        st.title("Python Assistant")
        st.caption("Powered by Google Gemini & Semantic Cache")

        # -------------------------------------------------------------
        # 💬 CHATGPT-STYLE LOCAL MULTI-SESSION CHAT HISTORY
        # -------------------------------------------------------------
        if "current_session_id" not in st.session_state:
            st.session_state["current_session_id"] = None

        # ➕ New Chat Button
        if st.button("➕ New Chat", use_container_width=True, type="primary", key="new_chat_btn"):
            st.session_state["chat_history"] = []
            st.session_state["current_session_id"] = None
            st.session_state["preset_query"] = None
            st.toast("Started new conversation!", icon="✨")
            st.rerun()

        st.markdown("### 💬 Recent Chats")
        
        # Fetch saved sessions from local disk backend store
        try:
            sess_res = requests.get(f"{backend_url}/api/sessions/list?user_id=local_user", timeout=5)
            if sess_res.status_code == 200:
                sessions = sess_res.json()
                if not sessions:
                    st.caption("*No saved conversations yet.*")
                else:
                    for s in sessions:
                        s_id = s.get("id")
                        s_title = s.get("title", "Conversation")
                        is_active = (s_id == st.session_state.get("current_session_id"))
                        
                        # Clean display title
                        display_label = f"📌 {s_title}" if is_active else f"💬 {s_title}"
                        
                        col_s_btn, col_s_del = st.columns([4, 1])
                        with col_s_btn:
                            if st.button(display_label, key=f"sess_btn_{s_id}", use_container_width=True):
                                # Load messages for this session
                                load_res = requests.get(f"{backend_url}/api/sessions/{s_id}?user_id=local_user", timeout=5)
                                if load_res.status_code == 200:
                                    msgs = load_res.json()
                                    st.session_state["chat_history"] = msgs
                                    st.session_state["current_session_id"] = s_id
                                    st.rerun()

                        with col_s_del:
                            if st.button("🗑️", key=f"del_sess_{s_id}", help="Delete chat"):
                                requests.delete(f"{backend_url}/api/sessions/{s_id}?user_id=local_user", timeout=5)
                                if st.session_state.get("current_session_id") == s_id:
                                    st.session_state["chat_history"] = []
                                    st.session_state["current_session_id"] = None
                                st.toast("Chat deleted", icon="🗑️")
                                st.rerun()
        except Exception as e:
            st.caption(f"Could not load sessions: {e}")

        st.divider()



        # Chat & Cache Management Actions
        st.markdown("### Actions")


        if st.button("🧹 Clear Chat History", use_container_width=True, key="clear_chat_btn"):
            st.session_state["chat_history"] = []
            st.toast("Chat history cleared!", icon="🧹")
            st.rerun()

        # 📥 Export Chat History Button (Always visible)
        export_md = generate_markdown_export()
        st.download_button(
            label="📥 Download Chat (.md)",
            data=export_md,
            file_name="python_chat_history.md",
            mime="text/markdown",
            use_container_width=True,
            key="download_chat_btn"
        )

        if st.button("🗑️ Reset Cache", use_container_width=True, type="secondary", key="reset_cache_btn"):
            try:
                res = requests.post(f"{backend_url}/api/cache/clear", timeout=5)
                if res.status_code == 200:
                    st.toast("Cache cleared!", icon="✨")
                    st.rerun()
                else:
                    st.error("Failed to clear cache.")
            except Exception as e:
                st.error(f"Backend error: {e}")

        st.divider()

        # 🎛️ Semantic Cache Configuration
        st.markdown("### 🎛️ Cache Settings")
        
        if "similarity_threshold" not in st.session_state:
            st.session_state["similarity_threshold"] = 0.60

        current_thresh = st.session_state["similarity_threshold"]

        new_thresh = st.slider(
            "Similarity Threshold",
            min_value=0.00,
            max_value=1.00,
            value=float(current_thresh),
            step=0.05,
            help="Minimum cosine similarity score required for a Cache Hit (Score ≥ Threshold). LOWER values allow looser semantic matches and give HIGHER cache hits; HIGHER values require near-exact matches.",
            key="thresh_slider"
        )

        if new_thresh != current_thresh:
            st.session_state["similarity_threshold"] = new_thresh
            # Optionally sync with backend
            try:
                requests.post(f"{backend_url}/api/cache/threshold?threshold={new_thresh}", timeout=3)
            except Exception:
                pass
            st.toast(f"Threshold set to {new_thresh:.2f}", icon="🎛️")
            st.rerun()

        # Sensitivity Badge helper (Score >= Threshold)
        if new_thresh <= 0.60:
            st.caption("⚡ **Mode: High Cache Hits** (Looser semantic matching, higher hit rate)")
        elif new_thresh <= 0.80:
            st.caption("⚖️ **Mode: Balanced** (Optimal precision & cache hit balance)")
        else:
            st.caption("🎯 **Mode: Strict Match** (High precision, near-identical queries only)")

        st.divider()

        # Backend Connection Status
        try:
            health_res = requests.get(f"{backend_url}/", timeout=3)
            if health_res.status_code == 200:
                info = health_res.json()
                st.success("Backend: Connected")
                st.caption(f"Active Threshold: `{st.session_state['similarity_threshold']:.2f}`")
            else:
                st.warning("Backend: Offline")
        except Exception:
            st.error("Backend: Connection Error")

