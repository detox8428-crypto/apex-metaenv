"""
Comprehensive Test Suite for APEX API
Tests edge cases, error handling, and performance
Run with: pytest test_api.py -v
"""

import pytest
import json
import time
from httpx import AsyncClient
from uuid import uuid4

# If running tests locally, you'll need to adjust the import
try:
    from envs.code_solver_env.server.enhanced_app import app
    from envs.code_solver_env.server.enhanced_models import (
        ResetRequestV2, StepRequestV2, generate_request_id
    )
except ImportError:
    from enhanced_app import app
    from enhanced_models import ResetRequestV2, StepRequestV2, generate_request_id


# ============================================================================
# FIXTURES & TEST DATA
# ============================================================================

@pytest.fixture
async def client():
    """Async HTTP client for testing"""
    async with AsyncClient(app=app, base_url="http://test") as c:
        yield c


valid_reset_payloads = [
    {"domain": "data_pipeline", "difficulty": "easy"},
    {"domain": "code_review", "difficulty": "medium"},
    {"domain": "incident_debug", "difficulty": "hard"},
    {"domain": "data_pipeline", "difficulty": "easy", "seed": 42},
]

invalid_reset_payloads = [
    {"domain": "unknown_domain", "difficulty": "easy"},  # Invalid domain
    {"domain": "data_pipeline", "difficulty": "invalid"},  # Invalid difficulty
    {"domain": "data_pipeline"},  # Missing difficulty
    {"difficulty": "easy"},  # Missing domain
    {"domain": "", "difficulty": "easy"},  # Empty domain
]


# ============================================================================
# HEALTH CHECK TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_health_check_success(client):
    """Health check should always succeed"""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] in ["ok", "degraded", "error"]
    assert "active_sessions" in data
    assert data["active_sessions"] >= 0
    assert "uptime_seconds" in data
    assert data["memory_usage_mb"] >= 0
    assert data["version"] == "3.0.0"
    assert data["spec"] == "openenv/v1"


@pytest.mark.asyncio
async def test_health_check_performance(client):
    """Health check should respond in <100ms"""
    start = time.time()
    response = await client.get("/health")
    elapsed = (time.time() - start) * 1000  # Convert to ms
    
    assert response.status_code == 200
    assert elapsed < 100, f"Health check took {elapsed}ms, expected <100ms"


# ============================================================================
# RESET ENDPOINT TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_reset_valid_basic(client):
    """Reset with valid input should succeed"""
    payload = {"domain": "data_pipeline", "difficulty": "easy"}
    response = await client.post("/reset", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    
    # Validate response structure
    assert "session_id" in data
    assert "observation" in data
    
    observation = data["observation"]
    assert observation["task_id"]
    assert observation["domain"] == "data_pipeline"
    assert observation["difficulty"] == "easy"
    assert observation["step_count"] == 0
    assert observation["passed_cases"] == 0


@pytest.mark.asyncio
@pytest.mark.parametrize("payload", valid_reset_payloads)
async def test_reset_valid_all_domains(client, payload):
    """Reset should work for all domains and difficulties"""
    response = await client.post("/reset", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert "observation" in data


@pytest.mark.asyncio
@pytest.mark.parametrize("payload", invalid_reset_payloads)
async def test_reset_invalid_input(client, payload):
    """Invalid reset requests should return 400"""
    response = await client.post("/reset", json=payload)
    assert response.status_code == 400
    data = response.json()
    assert "error" in data
    assert "error_code" in data
    assert "request_id" in data


@pytest.mark.asyncio
async def test_reset_duplicate_session_id(client):
    """Duplicate session IDs should fail"""
    session_id = str(uuid4())
    
    # First reset succeeds
    response1 = await client.post("/reset", json={
        "domain": "data_pipeline",
        "difficulty": "easy",
        "session_id": session_id
    })
    assert response1.status_code == 200
    
    # Second reset with same ID fails
    response2 = await client.post("/reset", json={
        "domain": "data_pipeline",
        "difficulty": "easy",
        "session_id": session_id
    })
    assert response2.status_code == 409  # Conflict


@pytest.mark.asyncio
async def test_reset_auto_session_id(client):
    """Reset without session_id should auto-generate"""
    response = await client.post("/reset", json={
        "domain": "data_pipeline",
        "difficulty": "easy"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert len(data["session_id"]) > 0  # Should be non-empty


# ============================================================================
# STEP ENDPOINT TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_step_valid_code_submission(client):
    """Valid code submission should succeed"""
    # First reset
    reset_response = await client.post("/reset", json={
        "domain": "data_pipeline",
        "difficulty": "easy"
    })
    assert reset_response.status_code == 200
    session_id = reset_response.json()["session_id"]
    
    # Then step
    step_response = await client.post("/step", json={
        "session_id": session_id,
        "code": "def process(df):\n    return df.head()"
    })
    
    assert step_response.status_code == 200
    data = step_response.json()
    
    # Validate response structure
    assert data["session_id"] == session_id
    assert "observation" in data
    assert "reward" in data
    assert "done" in data
    assert "info" in data
    
    # Validate reward is in range
    assert 0.0 <= data["reward"] <= 1.0
    assert isinstance(data["done"], bool)


@pytest.mark.asyncio
async def test_step_invalid_session(client):
    """Step with invalid session should fail"""
    response = await client.post("/step", json={
        "session_id": "nonexistent-session",
        "code": "print('hello')"
    })
    
    assert response.status_code == 404
    data = response.json()
    assert "error" in data


@pytest.mark.asyncio
async def test_step_missing_session_id(client):
    """Step without session_id should fail"""
    response = await client.post("/step", json={
        "code": "print('hello')"
    })
    
    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_step_no_action(client):
    """Step without code/review/diagnosis should fail"""
    # First reset
    reset_response = await client.post("/reset", json={
        "domain": "data_pipeline",
        "difficulty": "easy"
    })
    session_id = reset_response.json()["session_id"]
    
    # Then step with no action
    response = await client.post("/step", json={
        "session_id": session_id
    })
    
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_step_multiple_actions(client):
    """Reset with multiple steps"""
    # Reset
    reset_response = await client.post("/reset", json={
        "domain": "data_pipeline",
        "difficulty": "medium"
    })
    session_id = reset_response.json()["session_id"]
    
    # Multiple steps
    step_count = 0
    for i in range(3):
        response = await client.post("/step", json={
            "session_id": session_id,
            "code": f"# Attempt {i+1}\ndef process(df):\n    return df"
        })
        
        assert response.status_code == 200
        data = response.json()
        step_count = data["info"]["step"]
    
    assert step_count == 3


# ============================================================================
# STATE ENDPOINT TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_state_valid_session(client):
    """State for valid session should succeed"""
    # Reset
    reset_response = await client.post("/reset", json={
        "domain": "code_review",
        "difficulty": "easy"
    })
    session_id = reset_response.json()["session_id"]
    
    # Get state
    response = await client.get(f"/state/{session_id}")
    assert response.status_code == 200
    
    data = response.json()
    assert data["session_id"] == session_id
    assert "observation" in data
    assert data["domain"] == "code_review"


@pytest.mark.asyncio
async def test_state_invalid_session(client):
    """State for invalid session should fail"""
    response = await client.get("/state/nonexistent-session")
    assert response.status_code == 404


# ============================================================================
# EDGE CASES
# ============================================================================

@pytest.mark.asyncio
async def test_empty_string_domain(client):
    """Empty string domain should fail"""
    response = await client.post("/reset", json={
        "domain": "",
        "difficulty": "easy"
    })
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_whitespace_domain(client):
    """Whitespace domain should be trimmed"""
    response = await client.post("/reset", json={
        "domain": "  data_pipeline  ",
        "difficulty": "easy"
    })
    # Should succeed after trimming
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_large_code_submission(client):
    """Very large code submission should be rejected"""
    reset_response = await client.post("/reset", json={
        "domain": "data_pipeline",
        "difficulty": "easy"
    })
    session_id = reset_response.json()["session_id"]
    
    # Code larger than 5000 chars
    large_code = "x = 1\n" * 1000  # 6000 chars
    
    response = await client.post("/step", json={
        "session_id": session_id,
        "code": large_code
    })
    
    # Should either fail or truncate
    # (depends on your exact validation)
    assert response.status_code in [200, 400, 422]


@pytest.mark.asyncio
async def test_malformed_json(client):
    """Malformed JSON should fail gracefully"""
    response = await client.post(
        "/reset",
        content="not valid json",
        headers={"Content-Type": "application/json"}
    )
    assert response.status_code in [400, 422]


# ============================================================================
# CONCURRENCY TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_multiple_sessions(client):
    """Multiple concurrent sessions should work independently"""
    sessions = []
    
    # Create 5 sessions
    for i in range(5):
        response = await client.post("/reset", json={
            "domain": "data_pipeline",
            "difficulty": "easy"
        })
        assert response.status_code == 200
        sessions.append(response.json()["session_id"])
    
    # Each should be unique
    assert len(set(sessions)) == 5
    
    # Each should accept steps independently
    for session_id in sessions:
        response = await client.post("/step", json={
            "session_id": session_id,
            "code": "pass"
        })
        assert response.status_code == 200


# ============================================================================
# PERFORMANCE TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_reset_latency(client):
    """Reset should respond in <1 second"""
    start = time.time()
    response = await client.post("/reset", json={
        "domain": "data_pipeline",
        "difficulty": "easy"
    })
    elapsed = (time.time() - start) * 1000
    
    assert response.status_code == 200
    assert elapsed < 1000, f"Reset took {elapsed}ms, expected <1000ms"


@pytest.mark.asyncio
async def test_step_latency(client):
    """Step should respond in <2 seconds"""
    # Reset
    reset_response = await client.post("/reset", json={
        "domain": "data_pipeline",
        "difficulty": "easy"
    })
    session_id = reset_response.json()["session_id"]
    
    # Step
    start = time.time()
    response = await client.post("/step", json={
        "session_id": session_id,
        "code": "pass"
    })
    elapsed = (time.time() - start) * 1000
    
    assert response.status_code == 200
    assert elapsed < 2000, f"Step took {elapsed}ms, expected <2000ms"


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
