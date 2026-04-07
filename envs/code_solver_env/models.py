"""Pydantic v2 models for APEX Engineering Benchmark - Multi-Domain Environment"""

from pydantic import BaseModel, Field
from typing import Optional, Literal, Dict, Any
from datetime import datetime


class PipelineAction(BaseModel):
    """Action: agent submits code or review for data pipeline task"""
    code: Optional[str] = Field(None, description="Python solution code (for solve/debug tasks)")
    review: Optional[dict] = Field(None, description="Code review JSON (for review tasks)")
    session_id: Optional[str] = Field(None, description="Session ID for multi-session mode")

    class Config:
        json_schema_extra = {
            "example": {
                "code": "import pandas as pd\n\ndef aggregate_sales(df: pd.DataFrame) -> pd.DataFrame:\n    return df.groupby('customer_id')['amount'].sum().sort_values(ascending=False).to_frame('total_amount').reset_index()",
                "session_id": "550e8400-e29b-41d4-a716-446655440000"
            }
        }



class DataSample(BaseModel):
    """Sample data for the pipeline task"""
    format: str = Field(..., description="Data format: csv, json, log")
    content: str = Field(..., description="Actual data content as string")
    description: str = Field(..., description="Human-readable description of data")

    class Config:
        json_schema_extra = {
            "example": {
                "format": "csv",
                "content": "customer_id,product,amount,date\nC001,laptop,1200.00,2024-01-15\nC001,mouse,25.00,2024-01-16",
                "description": "Sales transactions from January 2024"
            }
        }


class ReviewSubmission(BaseModel):
    """Agent's code review submission"""
    bug_location: str = Field(..., description="Line number or code section with bug (e.g., 'line 8')")
    bug_type: str = Field(
        ...,
        description="Type of bug: wrong_aggregation, wrong_merge, data_type_error, missing_null_handling, wrong_filter, off_by_one"
    )
    explanation: str = Field(..., description="Root cause explanation of the bug")
    fixed_code: str = Field(..., description="Corrected version of the function")

    class Config:
        json_schema_extra = {
            "example": {
                "bug_location": "line 8",
                "bug_type": "wrong_aggregation",
                "explanation": "The groupby is using 'product' instead of 'customer_id', which groups by product type rather than customer. This causes incorrect aggregation of total spend per customer.",
                "fixed_code": "def get_top_customers(df):\n    return df.groupby('customer_id')['amount'].sum().sort_values(ascending=False).head(5)"
            }
        }


class IncidentContext(BaseModel):
    """Incident report for incident debugging domain"""
    incident_report: str = Field(..., description="User-facing incident report (e.g., 'Service returning 500 since 14:32 UTC')")
    error_logs: str = Field(..., description="Relevant error log lines")
    deploy_info: Optional[str] = Field(None, description="Information about recent deployment")
    metrics: Optional[Dict[str, Any]] = Field(None, description="Metrics showing the problem (p99_latency, error_rate, memory, etc.)")

    class Config:
        json_schema_extra = {
            "example": {
                "incident_report": "Service returning HTTP 500 starting 14:32 UTC",
                "error_logs": "AttributeError: 'NoneType' has no attribute 'email'\n  File 'users.py', line 42, in get_user_profile",
                "deploy_info": "Deployment at 14:30 UTC changed User.get() method",
                "metrics": {
                    "error_rate": 0.15,
                    "p99_latency": 8000,
                    "error_type": "AttributeError"
                }
            }
        }


class CodeReviewSubmission(BaseModel):
    """Agent's code review submission for code_review domain"""
    problem_identified: str = Field(..., description="What specific problem exists in the code")
    production_impact: str = Field(..., description="Why this matters in production (scale, performance, data loss, etc.)")
    fix_approach: str = Field(..., description="How to fix it conceptually")
    fixed_code: str = Field(..., description="Corrected version of the code")

    class Config:
        json_schema_extra = {
            "example": {
                "problem_identified": "N+1 query pattern: loops through users and queries database once per user",
                "production_impact": "With 10,000 users, this makes 10,000 queries instead of 1, causing timeout at scale",
                "fix_approach": "Use batch query with IN clause or ORM bulk fetch",
                "fixed_code": "def get_user_orders(user_ids):\n    return db.query(Orders).filter(Orders.user_id.in_(user_ids)).all()"
            }
        }


class IncidentFixSubmission(BaseModel):
    """Agent submission for incident debugging"""
    diagnosis: str = Field(..., description="Analysis of what's wrong")
    fixed_code: str = Field(..., description="Corrected code")

    class Config:
        json_schema_extra = {
            "example": {
                "diagnosis": "User.get() returns None instead of raising exception, causing AttributeError on null email access",
                "fixed_code": "def get_user(user_id):\n    user = db.query(User).filter(User.id == user_id).first()\n    if not user:\n        raise UserNotFound(f'User {user_id} not found')\n    return user"
            }
        }



class PipelineObservation(BaseModel):
    """Observation: task description and current state (works for all 3 domains)"""
    task_id: str = Field(..., description="Unique task ID")
    domain: Literal["data_pipeline", "code_review", "incident_debug"] = Field(..., description="Domain: data_pipeline, code_review, or incident_debug")
    title: str = Field(..., description="Task title")
    description: str = Field(..., description="Detailed task description")
    task_type: Literal["solve", "review", "debug"] = Field(..., description="Task mode")
    difficulty: Literal["easy", "medium", "hard"] = Field(..., description="Task difficulty")
    function_signature: Optional[str] = Field(None, description="Required function signature (for data_pipeline domain)")
    data_sample: Optional[DataSample] = Field(None, description="Sample data for the task (for data_pipeline domain)")
    current_code: Optional[str] = Field(None, description="Broken code (for review/debug tasks)")
    incident: Optional[IncidentContext] = Field(None, description="Incident report (for incident_debug domain)")
    code_context: Optional[str] = Field(None, description="Broken code context (for code_review, incident_debug domains)")
    error_message: Optional[str] = Field(None, description="Crash message (for debug tasks)")
    visible_test_results: Optional[list] = Field(None, description="What passed/failed (visible only)")
    feedback: Optional[str] = Field(None, description="Step feedback like 'Test 1 passed. Test 2 failed...' or 'Fix revealed next symptom...'")
    passed_cases: int = Field(..., description="Number of passed test cases")
    total_cases: int = Field(..., description="Total number of test cases")
    step_count: int = Field(..., description="Number of steps taken in this episode")
    max_steps: int = Field(..., description="Maximum steps allowed per episode")

    class Config:
        json_schema_extra = {
            "example": {
                "task_id": "easy-solve-001",
                "domain": "data_pipeline",
                "title": "Sales CSV Aggregator",
                "description": "Write a function that aggregates total spend per customer from sales CSV",
                "task_type": "solve",
                "difficulty": "easy",
                "function_signature": "def aggregate_sales(df: pd.DataFrame) -> pd.DataFrame:",
                "data_sample": {
                    "format": "csv",
                    "content": "customer_id,product,amount\nC001,laptop,1200\nC001,mouse,25",
                    "description": "Sales transactions"
                },
                "passed_cases": 0,
                "total_cases": 5,
                "step_count": 0,
                "max_steps": 5
            }
        }



class StepResponse(BaseModel):
    """Response from step endpoint"""
    session_id: str = Field(..., description="Session ID for this interaction")
    observation: PipelineObservation = Field(..., description="Current task observation")
    reward: float = Field(..., description="Reward value (0.0 to 1.0)")
    done: bool = Field(..., description="Whether the episode is complete")
    info: dict = Field(..., description="Additional information (error details, breakdown, etc.)")

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "observation": {
                    "task_id": "easy-solve-001",
                    "title": "Sales CSV Aggregator",
                    "description": "Aggregate total spend per customer",
                    "task_type": "solve",
                    "difficulty": "easy",
                    "function_signature": "def aggregate_sales(df: pd.DataFrame) -> pd.DataFrame:",
                    "data_sample": {"format": "csv", "content": "...", "description": "..."},
                    "passed_cases": 3,
                    "total_cases": 5,
                    "step_count": 1,
                    "max_steps": 5
                },
                "reward": 0.6,
                "done": False,
                "info": {
                    "passed_cases": 3,
                    "total_cases": 5,
                    "success": False
                }
            }
        }


class ResetResponse(BaseModel):
    """Response from reset endpoint"""
    session_id: str = Field(..., description="New session ID for this episode")
    observation: PipelineObservation = Field(..., description="Initial task observation")

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "observation": {
                    "task_id": "easy-solve-001",
                    "title": "Sales CSV Aggregator",
                    "description": "Aggregate total spend per customer",
                    "task_type": "solve",
                    "difficulty": "easy",
                    "function_signature": "def aggregate_sales(df: pd.DataFrame) -> pd.DataFrame:",
                    "data_sample": {"format": "csv", "content": "...", "description": "..."},
                    "passed_cases": 0,
                    "total_cases": 5,
                    "step_count": 0,
                    "max_steps": 5
                }
            }
        }


class EnvState(BaseModel):
    """Internal session state"""
    session_id: str = Field(..., description="Unique session identifier")
    task_id: str = Field(..., description="Current task ID")
    domain: Literal["data_pipeline", "code_review", "incident_debug"] = Field(..., description="Domain")
    task_type: Literal["solve", "review", "debug"] = Field(..., description="Task mode")
    step_count: int = Field(..., description="Number of steps taken")
    max_steps: int = Field(..., description="Maximum steps per episode")
    best_reward: float = Field(..., description="Best reward achieved in this episode")
    episode_history: list[float] = Field(..., description="Reward per step in this episode")
    created_at: datetime = Field(..., description="When session was created")
    last_activity: datetime = Field(..., description="When session was last accessed")

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "task_id": "easy-solve-001",
                "domain": "data_pipeline",
                "task_type": "solve",
                "step_count": 3,
                "max_steps": 5,
                "best_reward": 0.8,
                "episode_history": [0.4, 0.6, 0.8],
                "created_at": "2024-04-03T12:00:00Z",
                "last_activity": "2024-04-03T12:00:05Z"
            }
        }


class SessionInfo(BaseModel):
    """Information about an active session"""
    session_id: str
    task_id: str
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
    contact: str = Field(default="Team APEX", description="Contact information")
    action_schema: dict = Field(..., description="JSON schema for actions")
    observation_schema: dict = Field(..., description="JSON schema for observations")
    transport: list[str] = Field(..., description="Supported transports (http, websocket)")
    endpoints: dict = Field(..., description="Available endpoints")
    reward: dict = Field(..., description="Reward specification")
    tasks: dict = Field(..., description="Task availability")
    capabilities: list[str] = Field(..., description="Environment capabilities")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "apex_data_pipeline",
                "version": "1.0.0",
                "spec": "openenv/v1",
                "description": "RL environment for data pipeline engineering tasks",
                "action_schema": {"type": "object", "properties": {"code": {"type": "string"}}},
                "observation_schema": {"type": "object", "properties": {"task_id": {"type": "string"}}},
                "transport": ["http", "websocket"],
                "endpoints": {
                    "reset": "POST /reset",
                    "step": "POST /step",
                    "state": "GET /state"
                },
                "reward": {"min": 0.0, "max": 1.0, "type": "continuous"},
                "tasks": {
                    "solve": 3,
                    "review": 3,
                    "debug": 3,
                    "difficulties": ["easy", "medium", "hard"]
                },
                "capabilities": ["multi_session", "sandboxed_execution"]
            }
        }


class TestCaseResult(BaseModel):
    """Result of a single test case execution"""
    case_index: int = Field(..., description="Test case index (0-based)")
    passed: bool = Field(..., description="Whether test passed")
    error: Optional[str] = Field(None, description="Error message if failed")
    time_ms: Optional[float] = Field(None, description="Execution time in milliseconds")


class EvaluateRequest(BaseModel):
    """Request to evaluate code"""
    code: str = Field(..., description="Code to evaluate")
    task_id: str = Field(..., description="Task ID to evaluate against")
    session_id: Optional[str] = Field(None, description="Session ID")


class EvaluationReport(BaseModel):
    """Detailed evaluation report"""
    task_id: str = Field(..., description="Task ID")
    passed_cases: int = Field(..., description="Number of passed test cases")
    total_cases: int = Field(..., description="Total test cases")
    test_results: list[TestCaseResult] = Field(..., description="Individual test results")
    reward: float = Field(..., description="Calculated reward")
    error_message: Optional[str] = Field(None, description="Any error message")


class ProblemScore(BaseModel):
    """Score for a problem"""
    problem_id: str = Field(..., description="Problem ID")
    reward: float = Field(..., description="Reward achieved")
    session_id: str = Field(..., description="Session that achieved it")
    timestamp: datetime = Field(..., description="When achieved")


class ProblemsListResponse(BaseModel):
    """Response with list of problems"""
    total: int = Field(..., description="Total number of problems")
    problems: list[dict] = Field(..., description="Problem definitions")


class ProblemDetail(BaseModel):
    """Detailed problem definition"""
    problem_id: str
    title: str
    description: str
    difficulty: str
    function_signature: str


class LeaderboardEntry(BaseModel):
    """Leaderboard entry"""
    rank: int = Field(..., description="Leaderboard rank")
    session_id: str = Field(..., description="Session ID")
    problem_id: str = Field(..., description="Problem ID")
    reward: float = Field(..., description="Reward achieved")
    timestamp: datetime = Field(..., description="When achieved")


class LeaderboardResponse(BaseModel):
    """Response with leaderboard data"""
    entries: list[LeaderboardEntry] = Field(..., description="Leaderboard entries")
    count: int = Field(..., description="Number of entries")



