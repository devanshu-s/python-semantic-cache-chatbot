import streamlit as st
import requests

def render_sidebar(backend_url: str):
    """
    Render a clean, minimal Streamlit sidebar for chat controls and backend health status.
    All thresholds and system configurations are managed exclusively by the backend.
    """
    with st.sidebar:
        st.image("https://img.icons8.com/color/96/python--v1.png", width=56)
        st.title("Python Assistant")

        st.caption("Powered by Google Gemini & Semantic Cache")

        st.divider()

        # Chat & Cache Management Actions
        st.markdown("### Actions")

        if st.button("🧹 Clear Chat History", use_container_width=True):
            st.session_state["chat_history"] = []
            st.toast("Chat history cleared!", icon="🧹")
            st.rerun()

        if st.button("🗑️ Reset Cache", use_container_width=True, type="secondary"):
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

        # Backend Connection Status
        try:
            health_res = requests.get(f"{backend_url}/", timeout=3)
            if health_res.status_code == 200:
                info = health_res.json()
                st.success("Backend: Connected")
                st.caption(f"Backend Threshold: `{info.get('similarity_threshold', 0.85)}`")
            else:
                st.warning("Backend: Offline")
        except Exception:
            st.error("Backend: Connection Error")
