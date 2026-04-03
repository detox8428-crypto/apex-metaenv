"""APEX Code Solver Client - HTTP and WebSocket support"""

import json
import asyncio
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass

import requests
import websockets
from websockets.client import WebSocketClientProtocol

logger = logging.getLogger(__name__)


@dataclass
class Episode:
    """Single episode tracking"""
    session_id: str
    problem_id: str
    steps: int
    best_reward: float
    best_solution_code: Optional[str] = None


class CodeSolverClient:
    """Client for APEX Code Solver with HTTP or WebSocket transport"""

    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        transport: str = "http",
        timeout: int = 30
    ):
        """
        Initialize client.
        
        Args:
            base_url: Server URL (e.g., http://localhost:8000 or ws://localhost:8000)
            transport: "http" (default) or "websocket"
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.transport = transport.lower()
        self.timeout = timeout
        self.session_id: Optional[str] = None
        self.ws: Optional[WebSocketClientProtocol] = None
        self._loop = None

        if self.transport not in ["http", "websocket"]:
            raise ValueError(f"transport must be 'http' or 'websocket', got {transport}")

    # ========================================================================
    # HTTP Transport
    # ========================================================================

    def _http_get(self, endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make HTTP GET request"""
        url = f"{self.base_url}{endpoint}"
        response = requests.get(url, params=params, timeout=self.timeout)
        response.raise_for_status()
        return response.json()

    def _http_post(self, endpoint: str, json_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make HTTP POST request"""
        url = f"{self.base_url}{endpoint}"
        response = requests.post(url, json=json_data, timeout=self.timeout)
        response.raise_for_status()
        return response.json()

    def _http_delete(self, endpoint: str) -> Dict[str, Any]:
        """Make HTTP DELETE request"""
        url = f"{self.base_url}{endpoint}"
        response = requests.delete(url, timeout=self.timeout)
        response.raise_for_status()
        return response.json()

    # ========================================================================
    # Public API
    # ========================================================================

    def reset(
        self,
        difficulty: Optional[str] = None,
        mode: str = "mixed",
        seed: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Reset environment and start new episode.
        
        Args:
            difficulty: "easy", "medium", "hard", or None for any
            mode: "canonical", "procedural", or "mixed"
            seed: Seed for procedural generation (optional)
            
        Returns:
            {"session_id": "...", "observation": {...}}
        """
        if self.transport == "http":
            params = {
                "difficulty": difficulty,
                "mode": mode,
                "seed": seed
            }
            response = self._http_get("/reset", params={k: v for k, v in params.items() if v is not None})
        else:
            # WebSocket
            raise NotImplementedError("Use reset_async() for WebSocket transport")

        self.session_id = response.get("session_id")
        return response

    async def reset_async(
        self,
        difficulty: Optional[str] = None,
        mode: str = "mixed",
        seed: Optional[int] = None
    ) -> Dict[str, Any]:
        """Reset environment (async, works with both transports)"""
        if self.transport == "http":
            return await self._run_async(self.reset, difficulty, mode, seed)
        else:
            # WebSocket
            await self._ensure_ws_connected()
            message = {
                "type": "reset",
                "difficulty": difficulty,
                "mode": mode,
                "seed": seed
            }
            await self.ws.send(json.dumps(message))
            response = json.loads(await self.ws.recv())
            self.session_id = response.get("session_id")
            return response

    def step(self, code: str) -> Dict[str, Any]:
        """
        Execute code and get results.
        
        Args:
            code: Python solution code
            
        Returns:
            {"observation": {...}, "reward": 0.5, "terminated": False, ...}
        """
        if self.transport == "http":
            params = {"session_id": self.session_id}
            payload = {"code": code, "session_id": self.session_id}
            response = self._http_post("/step", payload)
        else:
            raise NotImplementedError("Use step_async() for WebSocket transport")

        return response

    async def step_async(self, code: str) -> Dict[str, Any]:
        """Execute code (async, works with both transports)"""
        if self.transport == "http":
            return await self._run_async(self.step, code)
        else:
            # WebSocket
            await self._ensure_ws_connected()
            message = {
                "type": "step",
                "code": code
            }
            await self.ws.send(json.dumps(message))
            response = json.loads(await self.ws.recv())
            return response

    def get_state(self) -> Dict[str, Any]:
        """Get current session state"""
        if not self.session_id:
            raise ValueError("No active session - call reset() first")

        params = {"session_id": self.session_id}
        return self._http_get("/state", params)

    async def get_state_async(self) -> Dict[str, Any]:
        """Get state (async)"""
        if self.transport == "http":
            return await self._run_async(self.get_state)
        else:
            # WebSocket doesn't have a dedicated state endpoint
            raise NotImplementedError("Use HTTP transport for state queries")

    def get_health(self) -> Dict[str, Any]:
        """Get server health"""
        return self._http_get("/health")

    def get_manifest(self) -> Dict[str, Any]:
        """Get environment manifest and capabilities"""
        return self._http_get("/manifest")

    def list_problems(self, difficulty: Optional[str] = None) -> Dict[str, Any]:
        """List available problems"""
        params = {"difficulty": difficulty} if difficulty else {}
        return self._http_get("/problems", params)

    def get_problem(self, problem_id: str) -> Dict[str, Any]:
        """Get problem details"""
        return self._http_get(f"/problems/{problem_id}")

    def get_leaderboard(self, problem_id: Optional[str] = None) -> Dict[str, Any]:
        """Get leaderboard scores"""
        params = {"problem_id": problem_id} if problem_id else {}
        return self._http_get("/leaderboard", params)

    def list_sessions(self) -> Dict[str, Any]:
        """List active sessions"""
        return self._http_get("/sessions")

    def delete_session(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Delete a session"""
        sid = session_id or self.session_id
        if not sid:
            raise ValueError("No session ID provided")
        return self._http_delete(f"/sessions/{sid}")

    # ========================================================================
    # WebSocket Helper
    # ========================================================================

    async def _ensure_ws_connected(self):
        """Ensure WebSocket connection is established"""
        if self.ws is None or self.ws.closed:
            ws_url = self.base_url.replace("http", "ws", 1)
            # For now, connect without session - will get one on first reset
            if not self.session_id:
                self.session_id = "temp"  # Placeholder
            url = f"{ws_url}/ws/{self.session_id}"
            self.ws = await websockets.connect(url)
            logger.info(f"WebSocket connected to {url}")

    async def close_ws(self):
        """Close WebSocket connection"""
        if self.ws:
            await self.ws.close()
            self.ws = None
            logger.info("WebSocket closed")

    # ========================================================================
    # Async helpers
    # ========================================================================

    async def _run_async(self, fn, *args, **kwargs):
        """Run sync function in async context"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, fn, *args)

    # ========================================================================
    # Training loop helper
    # ========================================================================

    async def run_episode_async(
        self,
        agent_fn,
        difficulty: Optional[str] = None,
        mode: str = "mixed",
        max_steps: int = 10
    ) -> Episode:
        """
        Run a complete episode with an agent function.
        
        Args:
            agent_fn: Async function that takes observation dict and returns code string
            difficulty: Problem difficulty filter
            mode: Problem source mode
            max_steps: Max number of steps
            
        Returns:
            Episode object with results
        """
        # Reset
        reset_resp = await self.reset_async(difficulty=difficulty, mode=mode)
        session_id = reset_resp["session_id"]
        observation = reset_resp["observation"]
        problem_id = observation["problem_id"]

        best_reward = 0.0
        best_solution_code = None

        # Loop
        for step_num in range(max_steps):
            # Get agent's code
            code = await agent_fn(observation)

            # Step
            step_resp = await self.step_async(code)
            reward = step_resp["reward"]
            observation = step_resp["observation"]
            terminated = step_resp["terminated"]
            truncated = step_resp["truncated"]

            # Track best
            if reward > best_reward:
                best_reward = reward
                best_solution_code = code

            logger.info(
                f"Step {step_num + 1}/{max_steps}: reward={reward:.3f}, "
                f"passed={observation['passed_cases']}/{observation['total_cases']}"
            )

            if terminated:
                logger.info(f"Episode solved in {step_num + 1} steps!")
                break

            if truncated:
                logger.info(f"Episode truncated at {max_steps} steps")
                break

        return Episode(
            session_id=session_id,
            problem_id=problem_id,
            steps=step_num + 1,
            best_reward=best_reward,
            best_solution_code=best_solution_code
        )

    # ========================================================================
    # Context manager for WebSocket
    # ========================================================================

    async def __aenter__(self):
        """Async context manager entry"""
        if self.transport == "websocket":
            await self._ensure_ws_connected()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.transport == "websocket":
            await self.close_ws()


# ============================================================================
# Example usage
# ============================================================================

if __name__ == "__main__":
    # Synchronous HTTP example
    client = CodeSolverClient(base_url="http://localhost:8000", transport="http")

    # Get health
    health = client.get_health()
    print(f"Health: {health}")

    # Get manifest
    manifest = client.get_manifest()
    print(f"Environment: {manifest['name']} v{manifest['version']}")

    # Reset
    reset_resp = client.reset(difficulty="easy")
    print(f"Session: {reset_resp['session_id']}")
    print(f"Problem: {reset_resp['observation']['title']}")

    # Step
    code = """def two_sum(nums, target):
    for i in range(len(nums)):
        for j in range(i+1, len(nums)):
            if nums[i] + nums[j] == target:
                return [i, j]
    return []"""

    step_resp = client.step(code)
    print(f"Reward: {step_resp['reward']:.2f}")
    print(f"Passed: {step_resp['observation']['passed_cases']}/{step_resp['observation']['total_cases']}")
