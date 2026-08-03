import os
import sys
import streamlit as st

# Add project root directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from frontend.components.sidebar import render_sidebar
from frontend.components.chat_window import render_chat_window

# Streamlit Page Config
st.set_page_config(
    page_title="Python Chatbot",
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

# Render Minimal Sidebar
render_sidebar(BACKEND_URL)

# Render Simple Chatbot Interface
render_chat_window(BACKEND_URL)
