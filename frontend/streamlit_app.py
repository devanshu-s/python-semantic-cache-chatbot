import os
import sys
import streamlit as st

# Add project root directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from frontend.components.sidebar import render_sidebar
from frontend.components.chat_window import render_chat_window
from frontend.components.code_sandbox import render_code_sandbox

# Streamlit Page Config
st.set_page_config(
    page_title="Python Coding Assistant",
    page_icon="🐍",
    layout="wide",
    initial_sidebar_state="expanded"
)

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

# Load Custom CSS
css_path = os.path.join(os.path.dirname(__file__), "styles", "custom.css")
if os.path.exists(css_path):
    with open(css_path, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Render Sidebar Actions & Status
render_sidebar(BACKEND_URL)

# Split-Screen Workspace: Chatbot (Left) vs Python Code Sandbox (Right)
col_chat, col_sandbox = st.columns([1, 1], gap="medium")

with col_chat:
    render_chat_window(BACKEND_URL)

with col_sandbox:
    render_code_sandbox(BACKEND_URL)
