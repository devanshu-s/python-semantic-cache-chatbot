from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.services.leetcode_service import LeetCodeService, LeetCodeProblem

router = APIRouter(prefix="/api/leetcode", tags=["LeetCode"])
leetcode_service = LeetCodeService()

class FetchLeetCodeRequest(BaseModel):
    url_or_title: str

@router.post("/fetch", response_model=LeetCodeProblem)
async def fetch_leetcode_problem(payload: FetchLeetCodeRequest):
    """
    Fetch LeetCode problem description, difficulty, starter code, and constraints
    from LeetCode URL or problem title.
    """
    if not payload.url_or_title or not payload.url_or_title.strip():
        raise HTTPException(status_code=400, detail="LeetCode URL or problem title is required.")

    problem = leetcode_service.fetch_problem(payload.url_or_title.strip())
    return problem
