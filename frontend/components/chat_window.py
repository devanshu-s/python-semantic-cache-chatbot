import re
import requests
import streamlit as st
from typing import List

def extract_python_code(content: str) -> str:
    """Extract Python code blocks enclosed in ```python ... ``` or ``` ... ``` from markdown string."""
    # Match ```python, ```py, ```Python (case-insensitive)
    matches = re.findall(r"```(?:python|py)\s*\n?(.*?)\n?```", content, re.DOTALL | re.IGNORECASE)
    if matches:
        return "\n\n".join(m.strip() for m in matches if m.strip())
    # Fallback to generic ``` code blocks
    matches_generic = re.findall(r"```\s*\n?(.*?)\n?```", content, re.DOTALL)
    if matches_generic:
        return "\n\n".join(m.strip() for m in matches_generic if m.strip())
    return ""


def get_followup_suggestions(last_query: str, last_response: str) -> List[str]:
    """
    Dynamically derive topic-relevant follow-up suggestions based on the user query context.
    """
    q = last_query.lower()
    
    if any(w in q for w in ["list", "reverse", "flip", "slice"]):
        return [
            "Difference between .reverse() and [::-1]?",
            "What is the time complexity of list slicing?",
            "How to reverse a list of dictionaries?"
        ]
    elif any(w in q for w in ["file", "read", "line"]):
        return [
            "How to handle FileNotFoundError with try-except?",
            "Difference between read() and readlines()?",
            "How to read JSON files in Python?"
        ]
    elif any(w in q for w in ["dict", "dictionary", "key", "value"]):
        return [
            "How to merge two dictionaries in Python 3.9+?",
            "What is dictionary comprehension syntax?",
            "How to sort a dictionary by values?"
        ]
    elif "comprehension" in q:
        return [
            "Difference between list and generator comprehension?",
            "How to use nested loops in list comprehension?",
            "When should I avoid list comprehensions?"
        ]
    elif any(w in q for w in ["llm", "megatron", "model", "ai", "pytorch"]):
        return [
            "How to load PyTorch models on GPU?",
            "What is tensor parallelism in LLM training?",
            "How do I use HuggingFace transformers?"
        ]
    else:
        return [
            "Can you explain this step-by-step with code?",
            "What are common edge cases to watch out for?",
            "How to optimize performance for this solution?"
        ]


def render_chat_window(backend_url: str):
    """
    Render a clean, simple, conversational chat interface with dynamic follow-up suggestions and code copy buttons.
    """
    st.markdown("## 💬 Python AI Chatbot")
    st.caption("Ask any Python programming question. Previous context is remembered across turns.")

    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []

    # Quick Conversation Suggestion Chips (if chat is empty)
    if not st.session_state["chat_history"]:
        st.markdown("**Suggested Topics:**")
        chip_col1, chip_col2 = st.columns(2)
        
        with chip_col1:
            if st.button("Reverse a List", use_container_width=True, key="init_chip_1"):
                st.session_state["preset_query"] = "How do I reverse a list in Python?"
                st.rerun()

            if st.button("Read File Line-by-Line", use_container_width=True, key="init_chip_2"):
                st.session_state["preset_query"] = "What is the best way to read a text file line by line in Python?"
                st.rerun()

        with chip_col2:
            if st.button("Dictionary Iteration", use_container_width=True, key="init_chip_3"):
                st.session_state["preset_query"] = "How do I iterate over keys and values in a Python dictionary?"
                st.rerun()

            if st.button("List Comprehension", use_container_width=True, key="init_chip_4"):
                st.session_state["preset_query"] = "Explain list comprehension syntax in Python with code examples"
                st.rerun()

        # 🌐 LeetCode Problem URL / Title Auto-Fetcher
        st.markdown("<div style='margin-top: 14px;'></div>", unsafe_allow_html=True)
        st.markdown("**🌐 Auto-Fetch LeetCode Problem:**")
        
        col_lc_input, col_lc_btn = st.columns([3.2, 1.2])
        with col_lc_input:
            lc_input = st.text_input(
                label="LeetCode URL or Problem Title",
                placeholder="e.g. https://leetcode.com/problems/two-sum/ or 'Two Sum'",
                label_visibility="collapsed",
                key="lc_fetch_input"
            )
        with col_lc_btn:
            fetch_btn = st.button("⚡ Fetch", use_container_width=True, key="lc_fetch_submit_btn", type="secondary")

        if fetch_btn and lc_input.strip():
            with st.spinner("🔍 Fetching problem details from LeetCode..."):
                try:
                    res = requests.post(f"{backend_url}/api/leetcode/fetch", json={"url_or_title": lc_input.strip()}, timeout=15)
                    if res.status_code == 200:
                        data = res.json()
                        st.session_state["preset_query"] = data.get("formatted_prompt", "")
                        # Prepopulate sandbox starter code if available
                        if data.get("python_starter_code"):
                            st.session_state["sandbox_code"] = data["python_starter_code"]
                        st.toast(f"Fetched '{data.get('title')}' ({data.get('difficulty')})!", icon="🌐")
                        st.rerun()
                    else:
                        st.error("Could not fetch LeetCode problem. Please check the URL or title.")
                except Exception as e:
                    st.error(f"Error fetching problem: {e}")


    # Check for preset query trigger
    preset = st.session_state.pop("preset_query", None)

    # Display Chat Messages
    for idx, message in enumerate(st.session_state["chat_history"]):
        role = message["role"]
        avatar = "👤" if role == "user" else "🐍"
        
        with st.chat_message(role, avatar=avatar):
            st.markdown(message["content"])
            
            # Display clean status badge and Copy Code button for Assistant responses
            if role == "assistant":
                extracted_code = extract_python_code(message["content"])
                
                col_badge, col_copy = st.columns([2, 1])
                
                with col_badge:
                    if "metadata" in message:
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

                with col_copy:
                    if extracted_code:
                        if st.button("📋 Copy to Code Box", key=f"copy_code_btn_{idx}", use_container_width=True):
                            st.session_state["sandbox_code"] = extracted_code
                            # Pre-load test cases into sandbox
                            try:
                                res = requests.post(f"{backend_url}/api/test-cases/generate", json={"code": extracted_code}, timeout=15)
                                if res.status_code == 200:
                                    data = res.json()
                                    st.session_state["sandbox_test_cases"] = data.get("test_cases", [])
                                    st.session_state["sandbox_test_explanation"] = data.get("explanation", "")
                                    st.session_state["active_sandbox_view"] = "test_cases"
                                    st.session_state["test_results"] = None
                            except Exception:
                                st.session_state["sandbox_test_cases"] = []
                                st.session_state["sandbox_test_explanation"] = ""
                                st.session_state["test_results"] = None

                            st.toast("Code & Test Cases copied to Sandbox! Click '▶️ Run Code' or '🔍 Find Cases' to test.", icon="📋")
                            st.rerun()

    # Render Dynamic Follow-Up Prompt Suggestions under last Assistant response
    if st.session_state["chat_history"] and st.session_state["chat_history"][-1]["role"] == "assistant":
        last_assistant_msg = st.session_state["chat_history"][-1]
        last_user_msg = next((m["content"] for m in reversed(st.session_state["chat_history"]) if m["role"] == "user"), "")
        
        suggestions = get_followup_suggestions(last_user_msg, last_assistant_msg["content"])
        turn_id = len(st.session_state["chat_history"])
        
        st.markdown("**💡 Suggested Follow-Up Questions:**")
        for i, sug in enumerate(suggestions):
            if st.button(f"👉 {sug}", key=f"fup_{turn_id}_{i}", use_container_width=True):
                st.session_state["preset_query"] = sug
                st.rerun()

    # Input prompt box
    user_query = st.chat_input("Type your Python question here...")
    active_query = preset if preset else user_query

    if active_query:
        # Append User Message to Chat History
        user_msg = {"role": "user", "content": active_query}
        st.session_state["chat_history"].append(user_msg)

        # Auto-create local session and persist user message
        user_id = "local_user"
        if not st.session_state.get("current_session_id"):
            title = active_query[:35] + "..." if len(active_query) > 35 else active_query
            if "Solve the LeetCode problem:" in active_query:
                title = active_query.split("Solve the LeetCode problem:")[1].split("(")[0].strip("* \n") or "LeetCode Problem"
            try:
                c_res = requests.post(f"{backend_url}/api/sessions/create", json={"user_id": user_id, "title": title}, timeout=5)
                if c_res.status_code == 200:
                    st.session_state["current_session_id"] = c_res.json().get("id")
            except Exception:
                pass

        if st.session_state.get("current_session_id"):
            try:
                requests.post(
                    f"{backend_url}/api/sessions/{st.session_state['current_session_id']}/message?user_id={user_id}",
                    json={"role": "user", "content": active_query},
                    timeout=5
                )
            except Exception:
                pass

        # Prepare backend request payload
        history_payload = [
            {"role": m["role"], "content": m["content"]}
            for m in st.session_state["chat_history"][:-1]
        ]
        
        payload = {
            "query": active_query,
            "history": history_payload,
            "similarity_threshold": st.session_state.get("similarity_threshold", 0.60)
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

                    # Persist assistant message to local session
                    if st.session_state.get("current_session_id"):
                        try:
                            requests.post(
                                f"{backend_url}/api/sessions/{st.session_state['current_session_id']}/message?user_id={user_id}",
                                json={"role": "assistant", "content": response_text, "metadata": data},
                                timeout=5
                            )
                        except Exception:
                            pass

                    st.rerun()
                else:
                    st.error(f"Error from server: {res.text}")
            except Exception as e:
                st.error(f"Failed to communicate with backend: {e}")


