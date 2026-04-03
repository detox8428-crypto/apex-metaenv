"""Pydantic v2 models for APEX Code Solver Environment"""

from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime


class CodeAction(BaseModel):
    """Action: agent submits Python code to solve problem"""
    code: str = Field(..., description="Python solution code", examples=["def two_sum(nums, target):\n    return [0, 1]"])
    session_id: Optional[str] = Field(None, description="Session ID for multi-session mode")

    class Config:
        json_schema_extra = {
            "example": {
                "code": "def two_sum(nums, target):\n    for i in range(len(nums)):\n        for j in range(i+1, len(nums)):\n            if nums[i] + nums[j] == target:\n                return [i, j]\n    return []",
                "session_id": "550e8400-e29b-41d4-a716-446655440000"
            }
        }


class TestCaseResult(BaseModel):
    """Result of a single test case"""
    case_index: int = Field(..., description="Index of the test case (0-based)")
    passed: bool = Field(..., description="Whether the test case passed")
    error: Optional[str] = Field(None, description="Error message if test case failed")
    time_ms: Optional[float] = Field(None, description="Execution time in milliseconds")

    class Config:
        json_schema_extra = {
            "example": {
                "case_index": 0,
                "passed": True,
                "error": None,
                "time_ms": 1.2
            }
        }


class ProblemObservation(BaseModel):
    """Observation: problem statement and test results"""
    problem_id: str = Field(..., description="Unique problem ID")
    title: str = Field(..., description="Problem title")
    description: str = Field(..., description="Problem description")
    function_signature: str = Field(..., description="Required function signature")
    examples: str = Field(..., description="Input/output examples")
    constraints: str = Field(..., description="Problem constraints")
    difficulty: Literal["easy", "medium", "hard"] = Field(..., description="Problem difficulty")
    test_results: list[TestCaseResult] = Field(..., description="Detailed test case results")
    passed_cases: int = Field(..., description="Number of passed test cases")
    total_cases: int = Field(..., description="Total number of test cases")
    error_message: Optional[str] = Field(None, description="Syntax/runtime error if any")
    step_count: int = Field(..., description="Number of steps taken in this episode")
    max_steps: int = Field(..., description="Maximum steps allowed per episode")

    class Config:
        json_schema_extra = {
            "example": {
                "problem_id": "p001_v42",
                "title": "Two Sum",
                "description": "Given an array of integers nums and an integer target...",
                "function_signature": "def two_sum(nums, target):",
                "examples": "Example 1:\\nInput: nums = [2, 7, 11, 15], target = 9\\nOutput: [0, 1]",
                "constraints": "2 <= len(nums) <= 10^4",
                "difficulty": "easy",
                "test_results": [{"case_index": 0, "passed": True, "error": None, "time_ms": 1.2}],
                "passed_cases": 1,
                "total_cases": 5,
                "error_message": None,
                "step_count": 1,
                "max_steps": 10
            }
        }


class StepResponse(BaseModel):
    """Response from step endpoint"""
    session_id: str = Field(..., description="Session ID for this interaction")
    observation: ProblemObservation = Field(..., description="Current problem observation")
    reward: float = Field(..., description="Reward value (0.0 to 1.0)")
    terminated: bool = Field(..., description="Whether the episode is complete (solved or max steps)")
    truncated: bool = Field(..., description="Whether the episode was truncated (max steps reached)")
    info: dict = Field(..., description="Additional information (error details, efficiency bonus, etc.)")

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "observation": {
                    "problem_id": "p001_v42",
                    "title": "Two Sum",
                    "description": "Given an array...",
                    "function_signature": "def two_sum(nums, target):",
                    "examples": "Example 1...",
                    "constraints": "2 <= len(nums) <= 10^4",
                    "difficulty": "easy",
                    "test_results": [{"case_index": 0, "passed": True, "error": None, "time_ms": 1.2}],
                    "passed_cases": 1,
                    "total_cases": 5,
                    "error_message": None,
                    "step_count": 1,
                    "max_steps": 10
                },
                "reward": 0.2,
                "terminated": False,
                "truncated": False,
                "info": {
                    "passed_cases": 1,
                    "total_cases": 5,
                    "primary_reward": 0.2,
                    "efficiency_bonus": 0.0,
                    "attempt_penalty": -0.02,
                    "final_reward": 0.18,
                    "error_type": None,
                    "error_message": None,
                    "time_ms_total": 1.2,
                    "code_lines": 8
                }
            }
        }


class ResetResponse(BaseModel):
    """Response from reset endpoint"""
    session_id: str = Field(..., description="New session ID for this episode")
    observation: ProblemObservation = Field(..., description="Initial problem observation")

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "observation": {
                    "problem_id": "p001_v42",
                    "title": "Two Sum",
                    "description": "Given an array...",
                    "function_signature": "def two_sum(nums, target):",
                    "examples": "Example 1...",
                    "constraints": "2 <= len(nums) <= 10^4",
                    "difficulty": "easy",
                    "test_results": [],
                    "passed_cases": 0,
                    "total_cases": 5,
                    "error_message": None,
                    "step_count": 0,
                    "max_steps": 10
                }
            }
        }


class EnvState(BaseModel):
    """Internal session state"""
    session_id: str = Field(..., description="Unique session identifier")
    problem_id: str = Field(..., description="Current problem ID")
    step_count: int = Field(..., description="Number of steps taken")
    max_steps: int = Field(..., description="Maximum steps per episode")
    best_reward: float = Field(..., description="Best reward achieved in this episode")
    episode_history: list[float] = Field(..., description="Reward per step in this episode")
    created_at: datetime = Field(..., description="When session was created")
    last_activity: datetime = Field(..., description="When session was last accessed")
    problem_source: Literal["canonical", "procedural"] = Field(..., description="Source of problem")

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "problem_id": "p001_v42",
                "step_count": 3,
                "max_steps": 10,
                "best_reward": 0.6,
                "episode_history": [0.2, 0.4, 0.6],
                "created_at": "2024-04-03T12:00:00Z",
                "last_activity": "2024-04-03T12:00:05Z",
                "problem_source": "procedural"
            }
        }


class SessionInfo(BaseModel):
    """Information about an active session"""
    session_id: str
    problem_id: str
    step_count: int
    age_seconds: int
    best_reward: float


class SessionListResponse(BaseModel):
    """Response with list of active sessions"""
    active_count: int
    sessions: list[SessionInfo]


class ManifestResponse(BaseModel):
    """Environment manifest for auto-discovery"""
    name: str = Field(..., description="Environment name")
    version: str = Field(..., description="Environment version")
    spec: str = Field(..., description="Compliance spec (e.g., 'openenv/v1')")
    description: str = Field(..., description="Environment description")
    action_schema: dict = Field(..., description="JSON schema for actions")
    observation_schema: dict = Field(..., description="JSON schema for observations")
    transport: list[str] = Field(..., description="Supported transports (http, websocket)")
    endpoints: dict = Field(..., description="Available endpoints")
    reward: dict = Field(..., description="Reward specification")
    problems: dict = Field(..., description="Problem availability")
    capabilities: list[str] = Field(..., description="Environment capabilities")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "code_solver",
                "version": "2.0.0",
                "spec": "openenv/v1",
                "description": "RL environment for solving coding problems",
                "action_schema": {"type": "object", "properties": {"code": {"type": "string"}}},
                "observation_schema": {"type": "object", "properties": {"problem_id": {"type": "string"}}},
                "transport": ["http", "websocket"],
                "endpoints": {
                    "reset": "POST /reset",
                    "step": "POST /step",
                    "state": "GET /state",
                    "websocket": "ws://{host}/ws/{session_id}"
                },
                "reward": {"min": 0.0, "max": 1.0, "type": "continuous"},
                "problems": {
                    "canonical": 9,
                    "procedural": "infinite",
                    "difficulties": ["easy", "medium", "hard"]
                },
                "capabilities": ["multi_session", "procedural_generation", "sandboxed_execution", "websocket"]
            }
        }


class ProblemDetail(BaseModel):
    """Full problem details (sans test cases)"""
    problem_id: str
    title: str
    description: str
    function_signature: str
    examples: str
    constraints: str
    difficulty: Literal["easy", "medium", "hard"]
    total_cases: int
    source: Literal["canonical", "procedural"]


class ProblemsListResponse(BaseModel):
    """Response with available problems"""
    total: int
    canonical: int
    procedural: str  # "infinite"
    problems: list[ProblemDetail]


class LeaderboardEntry(BaseModel):
    """Single leaderboard entry"""
    rank: int
    problem_id: str
    problem_title: str
    reward: float
    session_id: str
    timestamp: datetime


class LeaderboardResponse(BaseModel):
    """Leaderboard response"""
    problem_id: Optional[str] = None
    entries: list[LeaderboardEntry]
    count: int
