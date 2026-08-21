import io
import sys
import requests
import streamlit as st
from typing import List, Dict, Any, Tuple

DEFAULT_SANDBOX_CODE = """# 🐍 Python Code Sandbox & Interpreter
# Supports both LeetCode (class Solution) and Generic Python code!

from typing import List, Optional, Dict

class Solution:
    def reverseList(self, nums: List[int]) -> List[int]:
        \"\"\"
        LeetCode-style Solution for array reversal.
        Handles empty arrays, single elements, and scale inputs.
        \"\"\"
        if not nums:
            return []
        return nums[::-1]

if __name__ == "__main__":
    solver = Solution()
    sample = [10, 20, 30, 40, 50]
    print("Input:", sample)
    print("Output:", solver.reverseList(sample))
"""

def execute_python_code(code: str, backend_url: str) -> Tuple[str, bool, str]:
    """
    Execute Python code safely in console and return (output_text, is_success, explanation).
    Seamlessly supports both LeetCode (class Solution) and Generic Python code.
    """
    import math, collections, heapq, bisect, itertools, functools, typing

    class ListNode:
        def __init__(self, val=0, next=None):
            self.val = val
            self.next = next
        def __repr__(self):
            res = []
            curr = self
            while curr:
                res.append(str(curr.val))
                curr = curr.next
            return "[" + ", ".join(res) + "]"

    class TreeNode:
        def __init__(self, val=0, left=None, right=None):
            self.val = val
            self.left = left
            self.right = right
        def __repr__(self):
            return f"TreeNode({self.val})"

    buffer = io.StringIO()
    old_stdout = sys.stdout
    is_success = True
    output_text = ""
    error_text = ""

    try:
        sys.stdout = buffer
        exec_globals = {
            "__name__": "__main__",
            "io": io,
            "sys": sys,
            "math": math,
            "collections": collections,
            "heapq": heapq,
            "bisect": bisect,
            "itertools": itertools,
            "functools": functools,
            "deque": collections.deque,
            "defaultdict": collections.defaultdict,
            "Counter": collections.Counter,
            "OrderedDict": collections.OrderedDict,
            "List": typing.List,
            "Dict": typing.Dict,
            "Tuple": typing.Tuple,
            "Set": typing.Set,
            "Optional": typing.Optional,
            "Union": typing.Union,
            "Any": typing.Any,
            "ListNode": ListNode,
            "TreeNode": TreeNode
        }
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

    return output_text, is_success, ""




def fetch_top_10_test_cases(code: str, backend_url: str) -> Dict[str, Any]:
    """Call backend to generate top 10 test cases using Gemini."""
    try:
        res = requests.post(
            f"{backend_url}/api/test-cases/generate",
            json={"code": code},
            timeout=25
        )
        if res.status_code == 200:
            return res.json()
        else:
            st.error(f"Failed to generate test cases: {res.text}")
            return {}
    except Exception as e:
        st.error(f"Connection error while fetching test cases: {e}")
        return {}


def evaluate_test_cases_api(code: str, test_cases: List[Dict[str, Any]], backend_url: str) -> Dict[str, Any]:
    """Call backend to evaluate user code against test cases."""
    try:
        res = requests.post(
            f"{backend_url}/api/test-cases/evaluate",
            json={"code": code, "test_cases": test_cases},
            timeout=20
        )
        if res.status_code == 200:
            return res.json()
        else:
            st.error(f"Failed to evaluate test cases: {res.text}")
            return {}
    except Exception as e:
        st.error(f"Connection error while evaluating test cases: {e}")
        return {}


def format_failure_debug_prompt(code: str, results: List[Dict[str, Any]], passed_count: int, total_count: int, user_notes: str = "") -> str:
    """
    Format a complete, structured prompt for the chatbot containing current code,
    failed test cases, passed cases, and user comments.
    """
    passed_cases = [r for r in results if r.get("passed")]
    failed_cases = [r for r in results if not r.get("passed")]

    lines = [
        "I ran my Python code against test cases and it failed some edge/test cases. Please analyze the failures, fix the bugs, and provide a corrected, complete solution that passes 100% of the test cases.\n",
        "### 🐍 My Current Code:",
        "```python",
        code.strip(),
        "```\n",
        f"### 📊 Test Results Summary: {passed_count} / {total_count} Passed ({len(failed_cases)} Failed)\n"
    ]

    if failed_cases:
        lines.append("### ❌ Failed Test Cases:")
        for fc in failed_cases:
            c_id = fc.get("id")
            c_name = fc.get("name")
            c_cat = str(fc.get("category", "")).upper()
            c_in = fc.get("input_args")
            c_exp = fc.get("expected_output")
            c_act = fc.get("actual_output")
            c_err = fc.get("error_message")

            lines.append(f"- **Case {c_id}: {c_name} [{c_cat}]**")
            lines.append(f"  - **Input**: `{c_in}`")
            lines.append(f"  - **Expected Output**: `{c_exp}`")
            lines.append(f"  - **Actual Output**: `{c_act}`")
            if c_err:
                lines.append(f"  - **Error Detail**: `{c_err}`")
        lines.append("")

    if passed_cases:
        lines.append("### ✅ Passed Test Cases:")
        for pc in passed_cases:
            lines.append(f"- Case {pc.get('id')}: {pc.get('name')} (Input: `{pc.get('input_args')}` -> Output: `{pc.get('actual_output')}`)")
        lines.append("")

    if user_notes:
        lines.append("### 💬 User Comments / Specific Constraints:")
        lines.append(user_notes)
        lines.append("")

    lines.append("### 🎯 Instruction for AI:")
    lines.append("1. Clearly explain why the current code failed on the failed test cases.")
    lines.append("2. Provide the revised, optimal, and 100% bug-free Python code solution inside a ```python ``` block.")

    return "\n".join(lines)


def render_code_sandbox(backend_url: str):
    """
    Render a comprehensive right-side Python Code Box / Compiler Sandbox.
    - 'Run Code': Executes the code in the terminal console only (no test cases).
    - 'Find Cases': Discovers top 10 edge test cases using Gemini and runs verification.
    """
    st.markdown("## 💻 Python Code Sandbox")
    st.caption("Test Python code or click 'Find Cases' to discover and verify top 10 test cases with Gemini.")

    if "sandbox_code" not in st.session_state:
        st.session_state["sandbox_code"] = DEFAULT_SANDBOX_CODE

    if "sandbox_test_cases" not in st.session_state:
        st.session_state["sandbox_test_cases"] = []

    if "sandbox_test_explanation" not in st.session_state:
        st.session_state["sandbox_test_explanation"] = ""

    if "test_results" not in st.session_state:
        st.session_state["test_results"] = None

    if "active_sandbox_view" not in st.session_state:
        st.session_state["active_sandbox_view"] = None

    # Code Editor Text Area directly bound to sandbox_code session state
    st.text_area(
        label="Python Code Editor",
        height=300,
        key="sandbox_code",
        help="Edit code or click 'Copy to Code Box' from the chatbot on the left."
    )

    # Action Buttons: Run Code, Find Cases, Reset Editor
    col_run, col_find, col_reset = st.columns([1.2, 1.2, 0.8])

    with col_run:
        run_clicked = st.button("▶️ Run Code", type="primary", use_container_width=True, key="run_sandbox_btn")

    with col_find:
        find_clicked = st.button("🔍 Find Cases", type="secondary", use_container_width=True, key="find_cases_btn", help="Use Gemini to find top 10 maximum test cases including edge cases.")

    with col_reset:
        if st.button("🔄 Reset", use_container_width=True, key="reset_sandbox_btn"):
            st.session_state["sandbox_code"] = DEFAULT_SANDBOX_CODE
            st.session_state["sandbox_test_cases"] = []
            st.session_state["sandbox_test_explanation"] = ""
            st.session_state["test_results"] = None
            st.session_state["active_sandbox_view"] = None
            st.session_state["last_console_output"] = None
            st.rerun()

    # 1. Handling 'Run Code' Action (Console only - DO NOT show test cases)
    if run_clicked:
        st.session_state["active_sandbox_view"] = "console"
        with st.spinner("Executing Python code..."):
            output_text, is_success, gemini_analysis = execute_python_code(st.session_state["sandbox_code"], backend_url)
            st.session_state["last_console_output"] = {
                "output": output_text,
                "is_success": is_success,
                "gemini_analysis": gemini_analysis
            }

    # 2. Handling 'Find Cases' Action (Find top 10 test cases with Gemini and evaluate)
    if find_clicked:
        st.session_state["active_sandbox_view"] = "test_cases"
        with st.spinner("🤖 Gemini is discovering top 10 maximum test cases (edge + scale) & evaluating..."):
            gen_data = fetch_top_10_test_cases(st.session_state["sandbox_code"], backend_url)
            if gen_data and "test_cases" in gen_data:
                st.session_state["sandbox_test_cases"] = gen_data["test_cases"]
                st.session_state["sandbox_test_explanation"] = gen_data.get("explanation", "")
                
                # Evaluate against user's code
                eval_res = evaluate_test_cases_api(st.session_state["sandbox_code"], gen_data["test_cases"], backend_url)
                st.session_state["test_results"] = eval_res
                st.toast(f"Discovered and evaluated {len(gen_data['test_cases'])} test cases!", icon="🔍")

    # ------------------ OUTPUT RENDERING ------------------

    # A. Display Test Cases View ONLY when 'Find Cases' was triggered
    if st.session_state.get("active_sandbox_view") == "test_cases":
        test_results = st.session_state.get("test_results")
        if test_results and "results" in test_results:
            passed = test_results.get("passed", 0)
            total = test_results.get("total", 0)
            failed = test_results.get("failed", total - passed)
            success_rate = test_results.get("success_rate", 0.0)
            exp = st.session_state.get("sandbox_test_explanation", "")

            if exp:
                st.info(f"**🔍 Gemini Test Coverage:** {exp}")

            # Top Scoreboard Banner
            if passed == total and total > 0:
                st.markdown(
                    f"""
                    <div class="test-scoreboard-success">
                        <div style="font-size: 1.25rem; font-weight: 700; color: #10b981; margin-bottom: 4px;">
                            🏆 MAXIMUM TEST CASES PASSED: {passed} / {total} (100% SUCCESS)
                        </div>
                        <div style="color: #94a3b8; font-size: 0.9rem;">
                            All standard cases, empty inputs, boundaries, and edge cases passed flawlessly!
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            elif passed > 0:
                st.markdown(
                    f"""
                    <div class="test-scoreboard-partial">
                        <div style="font-size: 1.25rem; font-weight: 700; color: #f59e0b; margin-bottom: 4px;">
                            ⚡ TEST CASES PASSED: {passed} / {total} ({success_rate:.1f}% Pass Rate)
                        </div>
                        <div style="color: #94a3b8; font-size: 0.9rem;">
                            {failed} test case(s) failed or encountered runtime differences.
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    f"""
                    <div class="test-scoreboard-fail">
                        <div style="font-size: 1.25rem; font-weight: 700; color: #ef4444; margin-bottom: 4px;">
                            ❌ TEST CASES FAILED: 0 / {total} Passed
                        </div>
                        <div style="color: #94a3b8; font-size: 0.9rem;">
                            Please verify syntax or check error traces below.
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            # Detailed Test Case Breakdown Cards
            st.markdown(f"### 🧪 Top 10 Test Cases ({passed}/{total} Passed)")
            for r in test_results["results"]:
                c_id = r.get("id", 1)
                c_name = r.get("name", f"Test {c_id}")
                c_cat = r.get("category", "edge_case")
                c_input = r.get("input_args", "")
                c_exp = r.get("expected_output", "")
                c_act = r.get("actual_output", "")
                c_passed = r.get("passed", False)
                c_time = r.get("execution_time_ms", 0.0)
                c_err = r.get("error_message")

                status_icon = "✅ PASS" if c_passed else "❌ FAIL"
                cat_label = f"[{c_cat.upper()}]"

                with st.expander(f"{status_icon} | Case {c_id}: {c_name} {cat_label} — {c_time:.1f}ms", expanded=(not c_passed)):
                    col_in, col_exp, col_act = st.columns(3)
                    with col_in:
                        st.markdown("**Input:**")
                        st.code(c_input, language="python")
                    with col_exp:
                        st.markdown("**Expected Output:**")
                        st.code(c_exp, language="python")
                    with col_act:
                        st.markdown("**Actual Output:**")
                        st.code(c_act, language="python")
                    if c_err:
                        st.error(f"Error Details: {c_err}")

            # 🛠️ If any test cases failed, provide Send to Chatbot for AI Fix with User Comments Area
            if failed > 0:
                st.divider()
                st.markdown("### 🛠️ Send Failures to AI Chatbot for Fix")
                st.caption("Automatically sends your code, passed & failed test cases, and custom instructions to the chatbot to generate a 100% working solution.")

                user_notes = st.text_area(
                    label="💬 Optional Comments / Notes for AI:",
                    placeholder="e.g., 'Please optimize time complexity to O(N)', 'Handle NoneType and empty strings gracefully', etc.",
                    key="failed_cases_user_notes",
                    height=75,
                    help="Add any custom constraints or hints for the chatbot."
                )

                if st.button("🚀 Send Code & Failed Cases to Chatbot", type="primary", use_container_width=True, key="send_failed_to_chat_btn"):
                    debug_prompt = format_failure_debug_prompt(
                        code=st.session_state["sandbox_code"],
                        results=test_results["results"],
                        passed_count=passed,
                        total_count=total,
                        user_notes=user_notes.strip()
                    )
                    st.session_state["preset_query"] = debug_prompt
                    st.toast("Transferred code and failed test cases to AI Chatbot!", icon="💬")
                    st.rerun()

        # Display Preloaded Test Cases from Chatbot before execution
        elif st.session_state.get("sandbox_test_cases"):
            test_cases = st.session_state["sandbox_test_cases"]
            exp = st.session_state.get("sandbox_test_explanation", "")

            st.markdown(f"### 🔍 Top {len(test_cases)} Test Cases Loaded from Chat")
            if exp:
                st.info(f"**Coverage Overview:** {exp}")

            for tc in test_cases:
                t_id = tc.get("id", 1)
                t_name = tc.get("name", f"Test Case {t_id}")
                t_cat = str(tc.get("category", "general")).upper()
                t_desc = tc.get("description", "")
                t_in = tc.get("input_args", "")
                t_out = tc.get("expected_output", "")

                with st.expander(f"Case {t_id}: {t_name} [{t_cat}]"):
                    if t_desc:
                        st.caption(f"💡 {t_desc}")
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.markdown("**Input:**")
                        st.code(t_in, language="python")
                    with col_b:
                        st.markdown("**Expected Output:**")
                        st.code(t_out, language="python")

            st.caption("👉 Click **🔍 Find Cases** to verify and run your solution against all these test cases!")


    # B. Display Execution Console ONLY when 'Run Code' was triggered (or default console output)
    elif st.session_state.get("active_sandbox_view") == "console" and "last_console_output" in st.session_state:
        console = st.session_state.get("last_console_output")
        if console:
            st.markdown("### 🖥️ Main Console Output")
            if console["is_success"]:
                st.success("✅ Clean Execution Output:")
                st.code(console["output"], language="text")
            else:
                st.error("❌ Execution Error:")
                st.code(console["output"], language="text")

            if console.get("gemini_analysis"):
                st.markdown("**🤖 Gemini Feedback:**")
                st.info(console["gemini_analysis"])
