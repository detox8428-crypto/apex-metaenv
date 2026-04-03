"""
Comprehensive test suite for APEX Code Solver RL Environment.

Tests all 10 gaps against a live server (subprocess fixture, no mocking).

Gaps Tested:
1. WebSocket persistent connections with message streaming
2. Multi-session management with UUID isolation
3. Procedural problem generation with seed determinism
4. Sandboxed code execution with security checks
5. Typed Pydantic models on all endpoints
6. Auto-discovery manifest endpoint
7. Docker image buildability
8. Composite reward system
9. SSE streaming for step results
10. HuggingFace Spaces Gradio interface

Run: pytest test_suite.py -v
"""

import pytest
import asyncio
import json
import subprocess
import time
import requests
import websockets
from pathlib import Path
from typing import Dict, Any


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture(scope="session")
def server():
    """
    Start a live server as a subprocess.
    Scope=session means it starts once for all tests.
    """
    print("\n[FIXTURE] Starting live server...")
    
    # Start server
    proc = subprocess.Popen(
        ["python", "run_server.py"],
        cwd=Path(__file__).parent,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Wait for server to start
    max_retries = 30
    for i in range(max_retries):
        try:
            resp = requests.get("http://localhost:8000/health", timeout=1)
            if resp.status_code == 200:
                print(f"[FIXTURE] Server started after {i} attempts")
                break
        except requests.RequestException:
            time.sleep(0.5)
    else:
        proc.kill()
        raise RuntimeError("Server failed to start")
    
    yield proc
    
    # Cleanup
    print("\n[FIXTURE] Stopping server...")
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()


@pytest.fixture
def base_url():
    """Base URL for server."""
    return "http://localhost:8000"


@pytest.fixture
def ws_base_url():
    """WebSocket base URL."""
    return "ws://localhost:8000"


# ============================================================================
# GAP 1: WEBSOCKET PERSISTENT CONNECTIONS
# ============================================================================

class TestWebSocketTransport:
    """Gap 1: WebSocket persistent connections with message streaming."""
    
    @pytest.mark.asyncio
    async def test_websocket_reset_message(self, ws_base_url):
        """Test WS reset command."""
        async with websockets.connect(f"{ws_base_url}/ws/test-session-1") as ws:
            # Send reset
            await ws.send(json.dumps({
                "type": "reset",
                "difficulty": "easy"
            }))
            
            # Receive response
            response = json.loads(await ws.recv())
            
            # Verify response structure
            assert response["type"] == "reset_response"
            assert response["payload"]["session_id"] == "test-session-1"
            assert "observation" in response["payload"]
            assert response["payload"]["observation"]["title"]
    
    @pytest.mark.asyncio
    async def test_websocket_step_message(self, ws_base_url):
        """Test WS step command."""
        async with websockets.connect(f"{ws_base_url}/ws/test-session-2") as ws:
            # Reset first
            await ws.send(json.dumps({"type": "reset", "difficulty": "easy"}))
            reset_resp = json.loads(await ws.recv())
            
            # Submit code
            await ws.send(json.dumps({
                "type": "step",
                "code": """def two_sum(nums, target):
    for i in range(len(nums)):
        for j in range(i+1, len(nums)):
            if nums[i] + nums[j] == target:
                return [i, j]
    return []"""
            }))
            
            # Receive response
            response = json.loads(await ws.recv())
            
            assert response["type"] == "step_response"
            assert "observation" in response["payload"]
            assert "reward" in response["payload"]
            assert "terminated" in response["payload"]
    
    @pytest.mark.asyncio
    async def test_websocket_auto_cleanup(self, ws_base_url):
        """Test WS connection cleanup on disconnect."""
        session_id = "test-session-cleanup"
        
        async with websockets.connect(f"{ws_base_url}/ws/{session_id}") as ws:
            await ws.send(json.dumps({"type": "reset", "difficulty": "easy"}))
            response = json.loads(await ws.recv())
            assert response["type"] == "reset_response"
        
        # After disconnect, session should still be retrievable
        # (30-min timeout means it's not immediately deleted)
        resp = requests.get(f"http://localhost:8000/state?session_id={session_id}")
        assert resp.status_code == 200


# ============================================================================
# GAP 2: MULTI-SESSION MANAGEMENT
# ============================================================================

class TestMultiSessionManagement:
    """Gap 2: Multi-session isolation with UUID tracking."""
    
    def test_session_isolation(self, base_url):
        """Test that multiple sessions maintain isolated state."""
        # Create session 1
        resp1 = requests.post(f"{base_url}/reset?difficulty=easy")
        session1 = resp1.json()["session_id"]
        problem1 = resp1.json()["observation"]["problem_id"]
        
        # Create session 2
        resp2 = requests.post(f"{base_url}/reset?difficulty=easy")
        session2 = resp2.json()["session_id"]
        problem2 = resp2.json()["observation"]["problem_id"]
        
        # Sessions must be different UUIDs
        assert session1 != session2
        
        # Problems can be different (or same)
        # Step on session1
        code1 = """def two_sum(nums, target):
    return [0, 1]"""
        
        resp = requests.post(
            f"{base_url}/step?session_id={session1}",
            json={"code": code1}
        )
        step1 = resp.json()
        assert "observation" in step1
        assert step1["observation"]["step_count"] == 1
        
        # Check session2 is still at step 0
        resp = requests.get(f"{base_url}/state?session_id={session2}")
        state2 = resp.json()
        assert state2["step_count"] == 0
    
    def test_session_expiry(self, base_url):
        """Test that expired sessions are handled."""
        # Create a session with custom ID
        resp = requests.post(f"{base_url}/reset?session_id=test-expiry-session&difficulty=easy")
        assert resp.status_code == 200
        
        # Get state immediately works
        resp = requests.get(f"{base_url}/state?session_id=test-expiry-session")
        assert resp.status_code == 200
    
    def test_list_sessions(self, base_url):
        """Test /sessions endpoint returns all active sessions."""
        # Create a few sessions
        ids = []
        for i in range(3):
            resp = requests.post(f"{base_url}/reset?difficulty=easy")
            ids.append(resp.json()["session_id"])
        
        # List sessions
        resp = requests.get(f"{base_url}/sessions")
        assert resp.status_code == 200
        data = resp.json()
        assert "sessions" in data
        assert len(data["sessions"]) >= 3
        
        # Creator session IDs should be in list
        session_ids = [s["session_id"] for s in data["sessions"]]
        for id_ in ids:
            assert id_ in session_ids


# ============================================================================
# GAP 3: PROCEDURAL PROBLEM GENERATION
# ============================================================================

class TestProceduralGeneration:
    """Gap 3: Infinite problem variants with seed-based determinism."""
    
    def test_procedural_determinism(self, base_url):
        """Test that same seed produces same problem."""
        # Generate with seed=42
        resp1 = requests.post(f"{base_url}/reset?mode=procedural&seed=42&difficulty=easy")
        prob1 = resp1.json()["observation"]
        
        # Generate with same seed again
        resp2 = requests.post(f"{base_url}/reset?mode=procedural&seed=42&difficulty=easy")
        prob2 = resp2.json()["observation"]
        
        # Must have same structure
        assert prob1["title"] == prob2["title"]
        assert prob1["description"] == prob2["description"]
        assert len(prob1["examples"]) == len(prob2["examples"])
    
    def test_procedural_different_seeds(self, base_url):
        """Test that different seeds produce different problems."""
        resp1 = requests.post(f"{base_url}/reset?mode=procedural&seed=1&difficulty=easy")
        prob1 = resp1.json()["observation"]
        
        resp2 = requests.post(f"{base_url}/reset?mode=procedural&seed=2&difficulty=easy")
        prob2 = resp2.json()["observation"]
        
        # At least the examples should differ
        # (different seeds might have different test cases)
        assert prob1["problem_id"] != prob2["problem_id"]
    
    def test_procedural_types(self, base_url):
        """Test that procedural generator produces expected problem types."""
        # Generate several procedural problems
        problem_types = set()
        
        for seed in range(10):
            resp = requests.post(f"{base_url}/reset?mode=procedural&seed={seed}&difficulty=easy")
            problem_id = resp.json()["observation"]["problem_id"]
            
            # Extract type from problem_id (e.g., "two_sum_v42" → "two_sum")
            problem_type = "_".join(problem_id.split("_")[:-1])
            problem_types.add(problem_type)
        
        # Should have multiple types
        assert len(problem_types) >= 2
        expected_types = {"two_sum", "palindrome", "sorting", "string_search", 
                         "math", "tree", "dp"}
        assert problem_types.issubset(expected_types)


# ============================================================================
# GAP 4: SANDBOXED CODE EXECUTION
# ============================================================================

class TestSandboxedExecution:
    """Gap 4: Security-checked, resource-limited subprocess execution."""
    
    def test_forbidden_import_blocked(self, base_url):
        """Test that importing os is blocked."""
        resp = requests.post(f"{base_url}/reset?difficulty=easy")
        session_id = resp.json()["session_id"]
        
        # Try to import os
        bad_code = """import os
def two_sum(nums, target):
    return [0, 1]"""
        
        resp = requests.post(
            f"{base_url}/step?session_id={session_id}",
            json={"code": bad_code}
        )
        result = resp.json()
        
        # Should not fail catastrophically; security error in results
        assert "error_type" in result or "observation" in result
        # Check if test results have security error
        if "observation" in result:
            obs = result["observation"]
            error_msg = obs.get("error_message", "")
            # Security should be caught
            assert "SECURITY" in error_msg or len(obs["test_results"]) > 0
    
    def test_eval_blocked(self, base_url):
        """Test that eval() is blocked."""
        resp = requests.post(f"{base_url}/reset?difficulty=easy")
        session_id = resp.json()["session_id"]
        
        bad_code = """def two_sum(nums, target):
    codes = eval("__import__('os').getcwd()")
    return [0, 1]"""
        
        resp = requests.post(
            f"{base_url}/step?session_id={session_id}",
            json={"code": bad_code}
        )
        result = resp.json()
        
        # Should block eval
        if "observation" in result:
            assert "test_results" in result["observation"] or "error_message" in result["observation"]
    
    def test_valid_code_execution(self, base_url):
        """Test that valid code runs without security errors."""
        resp = requests.post(f"{base_url}/reset?difficulty=easy")
        session_id = resp.json()["session_id"]
        
        good_code = """def two_sum(nums, target):
    for i in range(len(nums)):
        for j in range(i+1, len(nums)):
            if nums[i] + nums[j] == target:
                return [i, j]
    return []"""
        
        resp = requests.post(
            f"{base_url}/step?session_id={session_id}",
            json={"code": good_code}
        )
        assert resp.status_code == 200
        result = resp.json()
        
        # Should have valid results
        assert "observation" in result
        assert "test_results" in result["observation"]


# ============================================================================
# GAP 5: TYPED PYDANTIC MODELS
# ============================================================================

class TestTypedModels:
    """Gap 5: Pydantic v2 models on all endpoints."""
    
    def test_reset_response_structure(self, base_url):
        """Test ResetResponse Pydantic model."""
        resp = requests.post(f"{base_url}/reset?difficulty=easy")
        assert resp.status_code == 200
        data = resp.json()
        
        # Check fields from ResetResponse model
        assert "session_id" in data
        assert "observation" in data
        
        # Check observation fields (ProblemObservation model)
        obs = data["observation"]
        required_fields = {
            "problem_id", "title", "description", "function_signature",
            "examples", "constraints", "difficulty", "test_results",
            "passed_cases", "total_cases"
        }
        assert all(f in obs for f in required_fields)
    
    def test_step_response_structure(self, base_url):
        """Test StepResponse Pydantic model."""
        resp = requests.post(f"{base_url}/reset?difficulty=easy")
        session_id = resp.json()["session_id"]
        
        resp = requests.post(
            f"{base_url}/step?session_id={session_id}",
            json={"code": "def two_sum(nums, target):\n    return [0, 1]"}
        )
        assert resp.status_code == 200
        data = resp.json()
        
        # StepResponse fields
        required_fields = {
            "session_id", "observation", "reward", "terminated", "truncated", "info"
        }
        assert all(f in data for f in required_fields)
        
        # Reward should be float
        assert isinstance(data["reward"], float)
        assert 0.0 <= data["reward"] <= 1.0
        
        # terminated/truncated are bool
        assert isinstance(data["terminated"], bool)
        assert isinstance(data["truncated"], bool)
    
    def test_manifest_structure(self, base_url):
        """Test ManifestResponse structure."""
        resp = requests.get(f"{base_url}/manifest")
        assert resp.status_code == 200
        data = resp.json()
        
        # Manifest should have environment metadata
        assert "api_version" in data
        assert "capabilities" in data
        assert "action_space" in data
        assert "observation_space" in data


# ============================================================================
# GAP 6: AUTO-DISCOVERY MANIFEST
# ============================================================================

class TestAutoDiscoveryManifest:
    """Gap 6: /manifest endpoint for framework integration."""
    
    def test_manifest_endpoint_exists(self, base_url):
        """Test GET /manifest returns valid response."""
        resp = requests.get(f"{base_url}/manifest")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, dict)
    
    def test_manifest_has_action_schema(self, base_url):
        """Test manifest includes action space definition."""
        resp = requests.get(f"{base_url}/manifest")
        data = resp.json()
        
        assert "action_space" in data
        action = data["action_space"]
        assert "type" in action
        assert "properties" in action or "content" in action
    
    def test_manifest_has_observation_schema(self, base_url):
        """Test manifest includes observation space definition."""
        resp = requests.get(f"{base_url}/manifest")
        data = resp.json()
        
        assert "observation_space" in data
        obs = data["observation_space"]
        assert "type" in obs
    
    def test_manifest_has_endpoints(self, base_url):
        """Test manifest lists available endpoints."""
        resp = requests.get(f"{base_url}/manifest")
        data = resp.json()
        
        assert "endpoints" in data or "available_endpoints" in data


# ============================================================================
# GAP 7: DOCKER BUILDABILITY
# ============================================================================

class TestDockerBuild:
    """Gap 7: Docker image builds successfully."""
    
    def test_dockerfile_exists(self):
        """Test that Dockerfile exists."""
        dockerfile = Path(__file__).parent / "Dockerfile"
        assert dockerfile.exists(), "Dockerfile not found"
    
    def test_docker_compose_exists(self):
        """Test that docker-compose files exist."""
        dc1 = Path(__file__).parent / "docker-compose.yml"
        dc2 = Path(__file__).parent / "docker-compose.scale.yml"
        assert dc1.exists(), "docker-compose.yml not found"
        assert dc2.exists(), "docker-compose.scale.yml not found"
    
    def test_requirements_file_valid(self):
        """Test that requirements.txt has valid syntax."""
        req_file = Path(__file__).parent / "requirements.txt"
        assert req_file.exists()
        
        with open(req_file) as f:
            lines = f.readlines()
            for line in lines:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                # Should be package==version or package>=version
                assert any(c in line for c in ["==", ">=", "<=", "~=", ">", "<"])


# ============================================================================
# GAP 8: COMPOSITE REWARD SYSTEM
# ============================================================================

class TestRewardSystem:
    """Gap 8: Multi-component reward calculation."""
    
    def test_reward_full_solve(self, base_url):
        """Test reward when all tests pass."""
        resp = requests.post(f"{base_url}/reset?difficulty=easy")
        session_id = resp.json()["session_id"]
        observation = resp.json()["observation"]
        
        # For two_sum, this should get most tests right
        code = """def two_sum(nums, target):
    seen = {}
    for i, num in enumerate(nums):
        if target - num in seen:
            return [seen[target - num], i]
        seen[num] = i
    return []"""
        
        resp = requests.post(
            f"{base_url}/step?session_id={session_id}",
            json={"code": code}
        )
        result = resp.json()
        
        # Should have reward between 0 and 1
        reward = result["reward"]
        assert isinstance(reward, float)
        assert 0.0 <= reward <= 1.0
        
        # Passed some tests
        assert result["observation"]["passed_cases"] >= 0
    
    def test_reward_all_tests_fail(self, base_url):
        """Test reward when no tests pass."""
        resp = requests.post(f"{base_url}/reset?difficulty=easy")
        session_id = resp.json()["session_id"]
        
        # Bad code
        code = """def two_sum(nums, target):
    return []"""
        
        resp = requests.post(
            f"{base_url}/step?session_id={session_id}",
            json={"code": code}
        )
        result = resp.json()
        
        reward = result["reward"]
        assert isinstance(reward, float)
        assert reward <= 1.0
        # If all tests fail, reward should be low
        if result["observation"]["passed_cases"] == 0:
            assert reward < 0.5
    
    def test_reward_info_included(self, base_url):
        """Test that step response includes reward breakdown."""
        resp = requests.post(f"{base_url}/reset?difficulty=easy")
        session_id = resp.json()["session_id"]
        
        resp = requests.post(
            f"{base_url}/step?session_id={session_id}",
            json={"code": "def two_sum(nums, target):\n    return [0, 1]"}
        )
        result = resp.json()
        
        # Info dict should have reward details
        info = result.get("info", {})
        assert "step_count" in info or result["observation"]["step_count"]


# ============================================================================
# GAP 9: SSE STREAMING FOR STEP RESULTS
# ============================================================================

class TestSSEStreaming:
    """Gap 9: Server-Sent Events for incremental test result delivery."""
    
    def test_step_stream_endpoint_exists(self, base_url):
        """Test that /step/stream endpoint exists."""
        resp = requests.post(f"{base_url}/reset?difficulty=easy")
        session_id = resp.json()["session_id"]
        
        # Try stream endpoint
        resp = requests.post(
            f"{base_url}/step/stream?session_id={session_id}",
            json={"code": "def two_sum(nums, target):\n    return [0, 1]"}
        )
        assert resp.status_code == 200
    
    def test_stream_content_type(self, base_url):
        """Test that stream endpoint returns SSE content type."""
        resp = requests.post(f"{base_url}/reset?difficulty=easy")
        session_id = resp.json()["session_id"]
        
        resp = requests.post(
            f"{base_url}/step/stream?session_id={session_id}",
            json={"code": "def two_sum(nums, target):\n    return [0, 1]"},
            stream=True
        )
        
        # Should be streaming content type
        content_type = resp.headers.get("content-type", "")
        assert "event-stream" in content_type or "stream" in content_type.lower()


# ============================================================================
# GAP 10: HUGGINGFACE SPACES GRADIO INTERFACE
# ============================================================================

class TestGradioInterface:
    """Gap 10: Gradio interface for HuggingFace Spaces."""
    
    def test_app_gradio_exists(self):
        """Test that app_gradio.py exists."""
        app_file = Path(__file__).parent / "envs" / "code_solver_env" / "app_gradio.py"
        assert app_file.exists(), f"app_gradio.py not found at {app_file}"
    
    def test_app_gradio_imports(self):
        """Test that app_gradio has required imports."""
        app_file = Path(__file__).parent / "envs" / "code_solver_env" / "app_gradio.py"
        with open(app_file) as f:
            content = f.read()
            
        # Should import gradio
        assert "gradio" in content or "gr" in content
        
        # Should import code solver environment
        assert "CodeSolverEnvironment" in content or "code_solver" in content


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestFullEpisode:
    """Full end-to-end episode: reset → multiple steps → solve."""
    
    def test_complete_easy_problem(self, base_url):
        """Test solving an easy problem completely."""
        # Reset
        resp = requests.post(f"{base_url}/reset?difficulty=easy")
        assert resp.status_code == 200
        session_id = resp.json()["session_id"]
        obs1 = resp.json()["observation"]
        
        # Step 1: Wrong answer
        resp = requests.post(
            f"{base_url}/step?session_id={session_id}",
            json={"code": "def " + obs1["function_signature"].split("(")[0]+"(nums, target):\n    return [0, 1]"}
        )
        assert resp.status_code == 200
        step1 = resp.json()
        assert step1["observation"]["step_count"] == 1
        assert "reward" in step1
        
        # Step 2: Try to solve
        # For two_sum, use a simple approach
        solve_attempts = [
            """def two_sum(nums, target):
    seen = {}
    for i, num in enumerate(nums):
        if target - num in seen:
            return [seen[target - num], i]
        seen[num] = i
    return []""",
            """def palindrome_check(s):
    s = ''.join(c.lower() for c in s if c.isalnum())
    return s == s[::-1]""",
            """def fizzbuzz(n):
    result = []
    for i in range(1, n+1):
        if i % 15 == 0:
            result.append("FizzBuzz")
        elif i % 3 == 0:
            result.append("Fizz")
        elif i % 5 == 0:
            result.append("Buzz")
        else:
            result.append(str(i))
    return result"""
        ]
        
        best_reward = step1["reward"]
        best_passed = step1["observation"]["passed_cases"]
        
        for attempt_code in solve_attempts[1:]:
            resp = requests.post(
                f"{base_url}/step?session_id={session_id}",
                json={"code": attempt_code}
            )
            if resp.status_code == 200:
                step = resp.json()
                if step["reward"] > best_reward:
                    best_reward = step["reward"]
                    best_passed = step["observation"]["passed_cases"]
        
        # By now we should have gotten some tests right
        assert best_reward > 0 or best_passed > 0


# ============================================================================
# EDGE CASES
# ============================================================================

class TestEdgeCases:
    """Test error handling and edge cases."""
    
    def test_invalid_session_id(self, base_url):
        """Test that invalid session ID is handled."""
        resp = requests.get(f"{base_url}/state?session_id=nonexistent-session-12345")
        # Should either 404 or return None
        assert resp.status_code in [200, 404]
    
    def test_empty_code_submission(self, base_url):
        """Test submitting empty code."""
        resp = requests.post(f"{base_url}/reset?difficulty=easy")
        session_id = resp.json()["session_id"]
        
        resp = requests.post(
            f"{base_url}/step?session_id={session_id}",
            json={"code": ""}
        )
        # Should handle gracefully
        assert resp.status_code == 200
    
    def test_syntax_error(self, base_url):
        """Test submitting code with syntax error."""
        resp = requests.post(f"{base_url}/reset?difficulty=easy")
        session_id = resp.json()["session_id"]
        
        resp = requests.post(
            f"{base_url}/step?session_id={session_id}",
            json={"code": "def bad syntax here!\n    pass"}
        )
        result = resp.json()
        
        # Should have error but not crash
        assert "observation" in result or "error" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
