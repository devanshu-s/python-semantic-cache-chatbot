import pytest
from fastapi.testclient import TestClient
from backend.app import app
from backend.services.test_case_service import test_case_service
from backend.models.test_case_models import TestCaseItem

client = TestClient(app)

SAMPLE_PERFECT_CODE = """
def reverse_list(data: list) -> list:
    if not data:
        return []
    return data[::-1]
"""

SAMPLE_BUGGY_CODE = """
def reverse_list(data: list) -> list:
    # Fails on empty list by raising index error
    first = data[0]
    return data[::-1]
"""

def test_generate_top_10_test_cases():
    resp = test_case_service.generate_top_10_test_cases(SAMPLE_PERFECT_CODE)
    assert resp is not None
    assert len(resp.test_cases) == 10
    assert resp.function_name == "reverse_list"
    # Check that test case IDs are 1 to 10
    ids = [tc.id for tc in resp.test_cases]
    assert ids == list(range(1, 11))

def test_evaluate_perfect_code():
    gen_resp = test_case_service.generate_top_10_test_cases(SAMPLE_PERFECT_CODE)
    eval_resp = test_case_service.evaluate_test_cases(SAMPLE_PERFECT_CODE, gen_resp.test_cases)
    
    assert eval_resp.total == 10
    assert eval_resp.passed >= 8
    assert eval_resp.success_rate >= 80.0


def test_evaluate_buggy_code():
    gen_resp = test_case_service.generate_top_10_test_cases(SAMPLE_BUGGY_CODE)
    eval_resp = test_case_service.evaluate_test_cases(SAMPLE_BUGGY_CODE, gen_resp.test_cases)
    
    assert eval_resp.total == 10
    assert eval_resp.failed > 0
    assert eval_resp.passed < 10

def test_api_generate_and_evaluate_endpoints():
    # 1. Test /api/test-cases/generate
    gen_req = {"code": SAMPLE_PERFECT_CODE}
    res = client.post("/api/test-cases/generate", json=gen_req)
    assert res.status_code == 200
    data = res.json()
    assert "test_cases" in data
    assert len(data["test_cases"]) == 10

    # 2. Test /api/test-cases/evaluate
    eval_req = {
        "code": SAMPLE_PERFECT_CODE,
        "test_cases": data["test_cases"]
    }
    eval_res = client.post("/api/test-cases/evaluate", json=eval_req)
    assert eval_res.status_code == 200
    eval_data = eval_res.json()
    assert eval_data["total"] == 10
    assert eval_data["passed"] == 10
    assert eval_data["success_rate"] == 100.0
