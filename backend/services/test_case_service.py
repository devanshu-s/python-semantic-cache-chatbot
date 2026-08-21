import ast
import json
import re
import time
import io
import sys
from typing import List, Optional, Tuple, Any
from backend.config.settings import settings
from backend.models.test_case_models import (
    TestCaseItem,
    GenerateTestCasesResponse,
    TestCaseResult,
    EvaluateTestCasesResponse,
)
from backend.utils.logger import logger

class TestCaseService:
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.model_name = settings.GEMINI_MODEL

    def _extract_functions_from_code(self, code: str) -> List[str]:
        """Parse AST to find defined function names (both top-level and inside class Solution)."""
        funcs = []
        try:
            tree = ast.parse(code)
            # 1. Check for methods inside class Solution or other classes
            for node in tree.body:
                if isinstance(node, ast.ClassDef):
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef) and not item.name.startswith("_"):
                            funcs.append(item.name)
            # 2. Check for top-level functions
            for node in tree.body:
                if isinstance(node, ast.FunctionDef) and not node.name.startswith("_"):
                    funcs.append(node.name)
            if funcs:
                return funcs
        except Exception:
            pass

        # Fallback regex
        class_methods = re.findall(r"class\s+\w+.*?def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(", code, re.DOTALL)
        if class_methods:
            return [m for m in class_methods if not m.startswith("_")]
        generic_funcs = re.findall(r"def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(", code)
        return [f for f in generic_funcs if not f.startswith("_")]

    def generate_top_10_test_cases(self, code: str, query: Optional[str] = None) -> GenerateTestCasesResponse:
        """
        Use Google Gemini API to analyze Python code/problem and generate the top 10 test cases
        including standard, boundary, scale, empty, and edge cases.
        """
        detected_funcs = self._extract_functions_from_code(code)
        target_hint = f"Primary method/function appears to be `{detected_funcs[0]}`." if detected_funcs else ""

        system_instruction = (
            "You are an elite QA and software test engineering AI for Python and LeetCode problems. "
            "Your job is to analyze Python code or problem requirements (both LeetCode 'class Solution' and generic functions) "
            "and generate exactly 10 REALISTIC, PRACTICAL, and COMMONLY TESTED test cases for that specific problem. "
            "Focus on real-world inputs and standard interview / LeetCode test suites: "
            "- Common representative cases (typical valid inputs) "
            "- Realistic boundary cases (e.g., 0, single element, 2 elements) "
            "- Common edge cases (e.g., empty collection, negative numbers, zeros, duplicates, already sorted / reversed order) "
            "- Moderate scale test (e.g., 50-100 elements) "
            "Avoid unrealistic or bizarre inputs unless explicitly required by the problem. "
            "Always provide accurate, mathematically correct `expected_output` values according to standard problem semantics. "
            "You MUST respond ONLY with a valid JSON object matching the requested schema."
        )

        prompt = f"""
Analyze the following Python code and context, and generate the top 10 most realistic, practical, and commonly used test cases for it.
{target_hint}

Python Code:
```python
{code}
```

Optional Context / Problem:
{query or "Analyze the function and code to determine its problem specifications."}

Return a valid JSON object with the following schema:
{{
  "function_name": "<name of the primary method/function being tested, e.g. twoSum or solve>",
  "explanation": "<Brief 1-2 sentence overview of the realistic test coverage and edge cases covered>",
  "test_cases": [
    {{
      "id": 1,
      "name": "Standard Typical Input",
      "category": "standard",
      "input_args": "<clean valid python literal or expression matching function arguments, e.g. [1, 2, 3, 4] or 'hello' or nums=[2, 7, 11, 15], target=9>",
      "expected_output": "<exact python representation of the correct expected return value, e.g. [4, 3, 2, 1] or 'olleh' or [0, 1]>",
      "description": "<why this realistic case is important>"
    }},
    ... (exactly 10 realistic test cases: 
         1. Typical Standard Input, 
         2. Small Standard Input, 
         3. Empty Input / Zero, 
         4. Single Element Input, 
         5. Two Elements / Minimal Boundary, 
         6. Negative / Mixed Values, 
         7. Duplicate / Repeating Values, 
         8. Already Processed / Sorted / Symmetrical Input, 
         9. Reverse / Inverted Input, 
         10. Moderate Scaled Input)
  ]
}}

Ensure all 10 items have valid Python expressions in `input_args` and accurate `expected_output`.
"""


        # If no valid Gemini API key is configured, provide fallback test cases
        if not self.api_key or self.api_key == "your_gemini_api_key_here":
            return self._generate_heuristic_test_cases(code, detected_funcs)

        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=self.api_key)
            config = types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.2,
                response_mime_type="application/json"
            )

            response = client.models.generate_content(
                model=self.model_name,
                contents=[prompt],
                config=config
            )

            raw_text = response.text.strip()
            # Clean possible markdown wrapping if returned
            if raw_text.startswith("```json"):
                raw_text = raw_text[7:]
            if raw_text.startswith("```"):
                raw_text = raw_text[3:]
            if raw_text.endswith("```"):
                raw_text = raw_text[:-3]
            raw_text = raw_text.strip()

            parsed = json.loads(raw_text)
            
            func_name = parsed.get("function_name", "") or (detected_funcs[0] if detected_funcs else "solve")
            explanation = parsed.get("explanation", "Top 10 test cases covering standard inputs and edge cases.")
            cases_raw = parsed.get("test_cases", [])

            test_cases: List[TestCaseItem] = []
            for idx, c in enumerate(cases_raw[:10], 1):
                test_cases.append(
                    TestCaseItem(
                        id=idx,
                        name=c.get("name", f"Test Case {idx}"),
                        category=c.get("category", "general"),
                        input_args=str(c.get("input_args", "")),
                        expected_output=str(c.get("expected_output", "")),
                        description=c.get("description", "")
                    )
                )

            # If fewer than 10, pad with heuristic cases
            if len(test_cases) < 10:
                fallback = self._generate_heuristic_test_cases(code, detected_funcs)
                for f_case in fallback.test_cases:
                    if len(test_cases) >= 10:
                        break
                    f_case.id = len(test_cases) + 1
                    test_cases.append(f_case)

            return GenerateTestCasesResponse(
                function_name=func_name,
                test_cases=test_cases,
                explanation=explanation
            )

        except Exception as e:
            logger.error(f"Gemini test case generation error: {e}")
            return self._generate_heuristic_test_cases(code, detected_funcs)

    def _generate_heuristic_test_cases(self, code: str, funcs: List[str]) -> GenerateTestCasesResponse:
        """Fallback rule-based test case generator when Gemini API is unavailable."""
        target_func = funcs[0] if funcs else "solution"
        
        # Default suite covering 10 distinct standard & edge case scenarios
        templates = [
            ("Standard Case 1", "standard", "[10, 20, 30, 40, 50]", "[50, 40, 30, 20, 10]", "Standard baseline list"),
            ("Standard Case 2", "standard", "[1, 2, 3]", "[3, 2, 1]", "Small positive sequence"),
            ("Empty Input", "empty", "[]", "[]", "Testing empty collection edge case"),
            ("Single Element", "edge_case", "[42]", "[42]", "Single item boundary"),
            ("Two Elements", "boundary", "[1, 99]", "[99, 1]", "Minimum multi-element boundary"),
            ("Duplicate Elements", "edge_case", "[7, 7, 7, 7]", "[7, 7, 7, 7]", "Homogeneous values"),
            ("Negative Numbers", "edge_case", "[-10, -5, 0, 5, 10]", "[10, 5, 0, -5, -10]", "Negative and zero numbers"),
            ("Zero Values", "boundary", "[0, 0, 0]", "[0, 0, 0]", "Zero collection"),
            ("Large Input", "large", "list(range(100))", "list(range(99, -1, -1))", "Scalability test with 100 elements"),
            ("Alternating Values", "edge_case", "[1, -1, 1, -1]", "[-1, 1, -1, 1]", "Alternating polarity values")
        ]

        test_cases = [
            TestCaseItem(
                id=idx,
                name=t[0],
                category=t[1],
                input_args=t[2],
                expected_output=t[3],
                description=t[4]
            )
            for idx, t in enumerate(templates, 1)
        ]

        return GenerateTestCasesResponse(
            function_name=target_func,
            test_cases=test_cases,
            explanation="Heuristic top-10 test cases generated covering empty collections, single elements, negative values, duplicates, and scale boundaries."
        )

    def evaluate_test_cases(
        self,
        code: str,
        test_cases: List[TestCaseItem],
        function_name: Optional[str] = None
    ) -> EvaluateTestCasesResponse:
        """
        Execute user code in a controlled namespace against all test cases.
        Seamlessly supports both LeetCode (class Solution) and Generic functions.
        """
        import math
        import collections
        import heapq
        import bisect
        import itertools
        import functools
        import typing

        results: List[TestCaseResult] = []
        passed_count = 0

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

        # Create isolated execution namespace with standard LeetCode imports & structures
        exec_globals = {
            "__name__": "__main__",
            "io": io,
            "sys": sys,
            "json": json,
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
            "Deque": typing.Deque,
            "DefaultDict": typing.DefaultDict,
            "ListNode": ListNode,
            "TreeNode": TreeNode
        }

        # 1. Execute the user's code definition
        compile_buffer = io.StringIO()
        old_stdout = sys.stdout
        try:
            sys.stdout = compile_buffer
            exec(code, exec_globals)
        except Exception as e:
            sys.stdout = old_stdout
            for tc in test_cases:
                results.append(
                    TestCaseResult(
                        id=tc.id,
                        name=tc.name,
                        category=tc.category,
                        input_args=tc.input_args,
                        expected_output=tc.expected_output,
                        actual_output="Syntax / Execution Error",
                        passed=False,
                        execution_time_ms=0.0,
                        error_message=f"Code syntax error: {str(e)}"
                    )
                )
            return EvaluateTestCasesResponse(
                total=len(test_cases),
                passed=0,
                failed=len(test_cases),
                success_rate=0.0,
                results=results,
                summary_message=f"❌ 0 / {len(test_cases)} Test Cases Passed (Code failed to compile: {e})"
            )
        finally:
            sys.stdout = old_stdout

        # 2. Determine target function (Supports both LeetCode class Solution and Generic functions)
        target_fn = None
        
        # Check for LeetCode Solution class
        if "Solution" in exec_globals and isinstance(exec_globals["Solution"], type):
            try:
                solution_instance = exec_globals["Solution"]()
                # If specific function_name requested and on instance
                if function_name and hasattr(solution_instance, function_name) and callable(getattr(solution_instance, function_name)):
                    target_fn = getattr(solution_instance, function_name)
                else:
                    # Look for first non-dunder callable method on Solution
                    detected = self._extract_functions_from_code(code)
                    for fname in detected:
                        if hasattr(solution_instance, fname) and callable(getattr(solution_instance, fname)):
                            target_fn = getattr(solution_instance, fname)
                            break
                    if not target_fn:
                        for attr in dir(solution_instance):
                            if not attr.startswith("_") and callable(getattr(solution_instance, attr)):
                                target_fn = getattr(solution_instance, attr)
                                break
            except Exception as e:
                logger.error(f"Error instantiating Solution class: {e}")

        # Check for Generic top-level function
        if not target_fn:
            if function_name and function_name in exec_globals and callable(exec_globals[function_name]):
                target_fn = exec_globals[function_name]
            else:
                detected = self._extract_functions_from_code(code)
                for fname in detected:
                    if fname in exec_globals and callable(exec_globals[fname]):
                        target_fn = exec_globals[fname]
                        break


        # 3. Run each test case
        for tc in test_cases:
            start_t = time.perf_counter()
            actual_val = None
            err_msg = None
            passed = False
            captured_stdout = ""

            try:
                # Parse input arguments
                args_parsed = self._safe_eval_input(tc.input_args, exec_globals)
                
                # Execute target function if found
                if target_fn:
                    test_stdout = io.StringIO()
                    sys.stdout = test_stdout
                    try:
                        if isinstance(args_parsed, tuple):
                            actual_val = target_fn(*args_parsed)
                        elif isinstance(args_parsed, dict):
                            actual_val = target_fn(**args_parsed)
                        else:
                            actual_val = target_fn(args_parsed)
                        captured_stdout = test_stdout.getvalue().strip()
                    finally:
                        sys.stdout = old_stdout
                else:
                    # Script-based fallback
                    actual_val = exec_globals.get("result", compile_buffer.getvalue().strip())

                # Format actual output
                if actual_val is not None:
                    actual_output_str = repr(actual_val) if not isinstance(actual_val, str) else actual_val
                elif captured_stdout:
                    actual_output_str = captured_stdout
                else:
                    actual_output_str = "None"

                # Check equivalence
                passed = self._check_output_equivalence(actual_val, actual_output_str, tc.expected_output)

            except Exception as e:
                import traceback
                err_msg = str(e)
                actual_output_str = f"Runtime Error: {e}"
                passed = False

            exec_time_ms = (time.perf_counter() - start_t) * 1000.0

            if passed:
                passed_count += 1

            results.append(
                TestCaseResult(
                    id=tc.id,
                    name=tc.name,
                    category=tc.category,
                    input_args=tc.input_args,
                    expected_output=tc.expected_output,
                    actual_output=actual_output_str,
                    passed=passed,
                    execution_time_ms=round(exec_time_ms, 2),
                    error_message=err_msg
                )
            )

        total = len(test_cases)
        failed_count = total - passed_count
        success_rate = round((passed_count / total * 100.0) if total > 0 else 0.0, 1)

        if passed_count == total:
            summary = f"🎉 10 / 10 Test Cases Passed! (100% Success Rate - Maximum Test Cases Passed)"
        else:
            summary = f"⚡ {passed_count} / {total} Test Cases Passed ({success_rate}% Success Rate)"

        return EvaluateTestCasesResponse(
            total=total,
            passed=passed_count,
            failed=failed_count,
            success_rate=success_rate,
            results=results,
            summary_message=summary
        )

    def _safe_eval_input(self, input_str: str, context: dict) -> Any:
        """Parse input arguments string safely into Python object or tuple."""
        input_str = input_str.strip()
        if not input_str:
            return None

        # Check if keyword arguments format: "nums=[1,2], target=3"
        if "=" in input_str and not (input_str.startswith("{") or input_str.startswith("[")):
            try:
                # Wrap in fake function call to extract kwargs
                tree = ast.parse(f"f({input_str})")
                call_node = tree.body[0].value # type: ignore
                kwargs = {}
                args = []
                for kw in call_node.keywords:
                    kwargs[kw.arg] = ast.literal_eval(kw.value)
                for arg in call_node.args:
                    args.append(ast.literal_eval(arg))
                if kwargs and not args:
                    return kwargs
                if args and not kwargs:
                    return tuple(args) if len(args) > 1 else args[0]
            except Exception:
                pass

        # Try literal_eval
        try:
            return ast.literal_eval(input_str)
        except Exception:
            pass

        # Evaluate with builtins in context (e.g. range, list)
        try:
            return eval(input_str, {"__builtins__": __builtins__}, context)
        except Exception:
            return input_str

    def _check_output_equivalence(self, actual_val: Any, actual_str: str, expected_str: str) -> bool:
        """Smart comparison between actual output and expected output."""
        expected_str = expected_str.strip()
        actual_str = actual_str.strip()

        # Direct string equality
        if actual_str == expected_str:
            return True

        # Normalized string equality (ignore whitespace / quotes)
        if actual_str.replace("'", '"') == expected_str.replace("'", '"'):
            return True

        # Try evaluating expected output as Python object using literal_eval or safe eval
        try:
            expected_val = self._safe_eval_input(expected_str, {})
            if actual_val == expected_val:
                return True
            # Numeric precision comparison
            if isinstance(actual_val, (int, float)) and isinstance(expected_val, (int, float)):
                return abs(actual_val - expected_val) < 1e-6
            # List / sequence equality
            if isinstance(actual_val, list) and isinstance(expected_val, list):
                return actual_val == expected_val
        except Exception:
            pass

        # String representation lowercase comparison
        if actual_str.lower() == expected_str.lower():
            return True

        return False


test_case_service = TestCaseService()
