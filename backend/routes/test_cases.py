from fastapi import APIRouter, HTTPException, status
from backend.models.test_case_models import (
    GenerateTestCasesRequest,
    GenerateTestCasesResponse,
    EvaluateTestCasesRequest,
    EvaluateTestCasesResponse
)
from backend.services.test_case_service import test_case_service
from backend.utils.logger import logger

router = APIRouter(prefix="/api/test-cases", tags=["Test Cases"])

@router.post("/generate", response_model=GenerateTestCasesResponse)
async def generate_test_cases(request: GenerateTestCasesRequest) -> GenerateTestCasesResponse:
    """
    Analyze code and problem requirements using Gemini to generate top 10 test cases
    covering standard, boundary, scale, empty, and edge cases.
    """
    code = request.code.strip()
    if not code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Python code cannot be empty."
        )

    try:
        response = test_case_service.generate_top_10_test_cases(
            code=code,
            query=request.query
        )
        return response
    except Exception as e:
        logger.error(f"Error in /api/test-cases/generate: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate test cases: {str(e)}"
        )

@router.post("/evaluate", response_model=EvaluateTestCasesResponse)
async def evaluate_test_cases(request: EvaluateTestCasesRequest) -> EvaluateTestCasesResponse:
    """
    Execute user Python code against provided test cases and return detailed pass/fail scoreboard.
    """
    code = request.code.strip()
    if not code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Python code cannot be empty."
        )

    if not request.test_cases:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Test cases list cannot be empty."
        )

    try:
        response = test_case_service.evaluate_test_cases(
            code=code,
            test_cases=request.test_cases,
            function_name=request.function_name
        )
        return response
    except Exception as e:
        logger.error(f"Error in /api/test-cases/evaluate: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to evaluate test cases: {str(e)}"
        )
