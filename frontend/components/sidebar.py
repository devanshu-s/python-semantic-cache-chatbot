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
    Render a clean Streamlit sidebar for chat controls, chat export, and backend health status.
    """
    with st.sidebar:
        st.image("https://img.icons8.com/color/96/python--v1.png", width=56)
        st.title("Python Assistant")
        st.caption("Powered by Google Gemini & Semantic Cache")

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
            help="Adjust the minimum cosine similarity required for a Cache Hit. Lower values require closer query matches; higher values accept looser semantic matches.",
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

        # Sensitivity Badge helper
        if new_thresh < 0.40:
            st.caption("🎯 **Mode: Strict Match** (Higher precision, fewer cache hits)")
        elif new_thresh <= 0.70:
            st.caption("⚖️ **Mode: Balanced** (Optimal cache hit ratio)")
        else:
            st.caption("⚡ **Mode: High Cache Hits** (Looser semantic matching)")

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

