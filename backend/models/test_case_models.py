from pydantic import BaseModel, Field
from typing import List, Optional, Any

class TestCaseItem(BaseModel):
    __test__ = False
    id: int = Field(..., description="Test case sequence number (1-10)")
    name: str = Field(..., description="Short name or category, e.g. 'Standard Case', 'Empty Input', 'Negative Numbers'")
    category: str = Field(default="general", description="Category: 'standard', 'edge_case', 'boundary', 'empty', 'large'")
    input_args: str = Field(..., description="Input argument(s) as Python literal or standard representation")
    expected_output: str = Field(..., description="Expected return value or printed output as string")
    description: str = Field(default="", description="Explanation of why this test case is critical")

class GenerateTestCasesRequest(BaseModel):
    code: str = Field(..., description="Python code to analyze and generate test cases for")
    query: Optional[str] = Field(default=None, description="Optional problem prompt or context")

class GenerateTestCasesResponse(BaseModel):
    __test__ = False
    function_name: str = Field(default="", description="Identified primary function name")
    test_cases: List[TestCaseItem] = Field(default_factory=list, description="List of generated test cases (up to 10)")
    explanation: str = Field(default="", description="Summary of test coverage and edge cases considered")

class TestCaseResult(BaseModel):
    __test__ = False
    id: int
    name: str
    category: str
    input_args: str
    expected_output: str
    actual_output: str
    passed: bool
    execution_time_ms: float
    error_message: Optional[str] = None


class EvaluateTestCasesRequest(BaseModel):
    code: str = Field(..., description="Python code to execute")
    test_cases: List[TestCaseItem] = Field(..., description="List of test cases to run against the code")
    function_name: Optional[str] = Field(default=None, description="Optional target function name")

class EvaluateTestCasesResponse(BaseModel):
    total: int
    passed: int
    failed: int
    success_rate: float
    results: List[TestCaseResult]
    summary_message: str
