import io
import sys
import requests
import streamlit as st

DEFAULT_SANDBOX_CODE = """# 🐍 Python Code Sandbox & Interpreter
# Write or copy code here from the chatbot and click 'Run Code'

def demonstrate_solution():
    data = [10, 20, 30, 40, 50]
    reversed_list = data[::-1]
    print("Original list:", data)
    print("Reversed list:", reversed_list)
    return reversed_list

if __name__ == "__main__":
    demonstrate_solution()
"""

def execute_python_code(code: str, backend_url: str):
    """
    Execute Python code safely and return (output_text, is_success, gemini_explanation).
    """
    buffer = io.StringIO()
    old_stdout = sys.stdout
    is_success = True
    output_text = ""
    error_text = ""

    try:
        sys.stdout = buffer
        # Create safe execution environment
        exec_globals = {"__name__": "__main__"}
        exec(code, exec_globals)
        output_text = buffer.getvalue()
        if not output_text.strip():
            output_text = "Code executed cleanly with no print output."
    except Exception as e:
        is_success = False
        import traceback
        error_text = traceback.format_exc()
        output_text = f"Error: {e}\n\nTraceback:\n{error_text}"
    finally:
        sys.stdout = old_stdout

    # Optional Gemini Code Analysis
    gemini_analysis = ""
    try:
        if is_success:
            prompt = f"The following Python code ran successfully with output:\n{output_text}\n\nCode:\n{code}\n\nProvide a 2-line confirmation of what this code accomplished."
        else:
            prompt = f"The following Python code failed with error:\n{error_text}\n\nCode:\n{code}\n\nExplain in 2 simple lines why it failed and how to fix it."
            
        payload = {"query": prompt, "history": []}
        res = requests.post(f"{backend_url}/api/chat", json=payload, timeout=10)
        if res.status_code == 200:
            gemini_analysis = res.json().get("response", "")
    except Exception:
        pass

    return output_text, is_success, gemini_analysis


def render_code_sandbox(backend_url: str):
    """
    Render a right-side Python Code Box / Sandbox component.
    """
    st.markdown("## 💻 Python Code Sandbox")
    st.caption("Test, run, and evaluate Python code snippets side-by-side with your AI assistant.")

    if "sandbox_code" not in st.session_state:
        st.session_state["sandbox_code"] = DEFAULT_SANDBOX_CODE

    # Code Editor Text Area
    updated_code = st.text_area(
        label="Python Code Editor",
        value=st.session_state["sandbox_code"],
        height=320,
        key="sandbox_text_area",
        help="Edit code or click 'Copy to Code Box' from the chatbot on the left."
    )
    st.session_state["sandbox_code"] = updated_code

    col_run, col_reset = st.columns([2, 1])

    with col_run:
        run_clicked = st.button("▶️ Run Code", type="primary", use_container_width=True, key="run_sandbox_btn")

    with col_reset:
        if st.button("🔄 Reset Editor", use_container_width=True, key="reset_sandbox_btn"):
            st.session_state["sandbox_code"] = DEFAULT_SANDBOX_CODE
            st.rerun()

    # Output Terminal Window
    if run_clicked:
        with st.spinner("Executing Python code & evaluating with Gemini..."):
            output_text, is_success, gemini_analysis = execute_python_code(st.session_state["sandbox_code"], backend_url)
            
            st.markdown("### 🖥️ Execution Console")
            if is_success:
                st.success("✅ Execution Status: Working (Clean Success)")
                st.code(output_text, language="text")
            else:
                st.error("❌ Execution Status: Error Detected")
                st.code(output_text, language="text")

            if gemini_analysis:
                st.markdown("**🤖 Gemini Assistant Feedback:**")
                st.info(gemini_analysis)
