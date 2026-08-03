import streamlit as st
import requests

def render_chat_window(backend_url: str):
    """
    Render a clean, simple, conversational chat interface.
    """
    st.markdown("## 💬 Python AI Chatbot")
    st.caption("Ask any Python programming question. Previous context is remembered across turns.")

    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []

    # Quick Conversation Suggestion Chips (if chat is empty)
    if not st.session_state["chat_history"]:
        st.markdown("**Suggested Topics:**")
        chip_col1, chip_col2, chip_col3, chip_col4 = st.columns(4)
        
        with chip_col1:
            if st.button("Reverse a List", use_container_width=True):
                st.session_state["preset_query"] = "How do I reverse a list in Python?"
                st.rerun()

        with chip_col2:
            if st.button("Read File Line-by-Line", use_container_width=True):
                st.session_state["preset_query"] = "What is the best way to read a text file line by line in Python?"
                st.rerun()

        with chip_col3:
            if st.button("Dictionary Iteration", use_container_width=True):
                st.session_state["preset_query"] = "How do I iterate over keys and values in a Python dictionary?"
                st.rerun()

        with chip_col4:
            if st.button("List Comprehension", use_container_width=True):
                st.session_state["preset_query"] = "Explain list comprehension syntax in Python with code examples"
                st.rerun()

    # Check for preset query trigger
    preset = st.session_state.pop("preset_query", None)

    # Display Chat Messages
    for message in st.session_state["chat_history"]:
        role = message["role"]
        avatar = "👤" if role == "user" else "🐍"
        
        with st.chat_message(role, avatar=avatar):
            st.markdown(message["content"])
            
            # Display clean status badge for Assistant responses
            if role == "assistant" and "metadata" in message:
                meta = message["metadata"]
                is_cached = meta.get("is_cached", False)
                score = meta.get("similarity_score", 0.0)
                tot_lat = meta.get("total_latency_ms", 0.0)

                if is_cached:
                    st.markdown(
                        f"""
                        <div style="margin-top: 6px;">
                            <span class="badge-hit">⚡ CACHE HIT ({score * 100:.1f}%)</span>
                            <span style="font-size: 0.8rem; color: #94a3b8; margin-left: 8px;">{tot_lat:.1f} ms</span>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                else:
                    st.markdown(
                        f"""
                        <div style="margin-top: 6px;">
                            <span class="badge-miss">🤖 GEMINI RESPONSE</span>
                            <span style="font-size: 0.8rem; color: #94a3b8; margin-left: 8px;">{tot_lat:.1f} ms</span>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

    # Input prompt box
    user_query = st.chat_input("Type your Python question here...")
    active_query = preset if preset else user_query

    if active_query:
        # Append User Message to Chat History
        st.session_state["chat_history"].append({"role": "user", "content": active_query})

        # Prepare backend request payload
        history_payload = [
            {"role": m["role"], "content": m["content"]}
            for m in st.session_state["chat_history"][:-1]
        ]
        
        payload = {
            "query": active_query,
            "history": history_payload
        }

        with st.spinner("Thinking..."):
            try:
                res = requests.post(f"{backend_url}/api/chat", json=payload, timeout=30)
                if res.status_code == 200:
                    data = res.json()
                    response_text = data["response"]
                    
                    st.session_state["chat_history"].append({
                        "role": "assistant",
                        "content": response_text,
                        "metadata": data
                    })
                    st.rerun()
                else:
                    st.error(f"Error from server: {res.text}")
            except Exception as e:
                st.error(f"Failed to communicate with backend: {e}")
