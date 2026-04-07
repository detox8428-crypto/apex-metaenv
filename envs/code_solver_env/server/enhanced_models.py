"""
Enhanced Pydantic v2 Models for APEX API - Production Reliability
Adds robust validation, error handling, and input sanitization
"""

from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, Literal, Dict, Any, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# REQUEST MODELS - Enhanced Validation
# ============================================================================

class ResetRequestV2(BaseModel):
    """Enhanced Reset Request with full validation"""
    
    model_config = ConfigDict(str_strip_whitespace=True, extra='forbid')
    
    session_id: Optional[str] = Field(
        None,
        description="Optional custom session ID (if not provided, UUID generated)",
        min_length=1,
        max_length=100
    )
    domain: str = Field(
        "data_pipeline",
        description="Domain: data_pipeline, code_review, or incident_debug",
        examples=["data_pipeline", "code_review", "incident_debug"]
    )
    difficulty: str = Field(
        "easy",
        description="Difficulty: easy, medium, or hard",
        examples=["easy", "medium", "hard"]
    )
    seed: Optional[int] = Field(
        None,
        description="Random seed for reproducibility",
        ge=0,
        le=2**31 - 1
    )
    
    @field_validator('domain')
    @classmethod
    def validate_domain(cls, v: str) -> str:
        """Validate domain is one of allowed values"""
        allowed = ["data_pipeline", "code_review", "incident_debug"]
        v = v.lower().strip()
        if v not in allowed:
            raise ValueError(f"domain must be one of {allowed}, got: {v}")
        return v
    
    @field_validator('difficulty')
    @classmethod
    def validate_difficulty(cls, v: str) -> str:
        """Validate difficulty is one of allowed values"""
        allowed = ["easy", "medium", "hard"]
        v = v.lower().strip()
        if v not in allowed:
            raise ValueError(f"difficulty must be one of {allowed}, got: {v}")
        return v
    
    @field_validator('session_id')
    @classmethod
    def validate_session_id(cls, v: Optional[str]) -> Optional[str]:
        """Validate session_id format if provided"""
        if v is None:
            return v
        v = v.strip()
        if len(v) == 0:
            return None
        if not v.replace('-', '').replace('_', '').isalnum():
            raise ValueError(f"session_id must be alphanumeric (with - and _): {v}")
        return v


class StepRequestV2(BaseModel):
    """Enhanced Step Request with validation"""
    
    model_config = ConfigDict(str_strip_whitespace=True, extra='forbid')
    
    session_id: str = Field(
        ...,
        description="Session ID from reset response",
        min_length=1,
        max_length=100
    )
    code: Optional[str] = Field(
        None,
        description="Python code submission (for solve/debug domains)",
        max_length=5000
    )
    review: Optional[Dict[str, Any]] = Field(
        None,
        description="Code review submission (for code_review domain)"
    )
    diagnosis: Optional[str] = Field(
        None,
        description="Diagnosis text (for incident_debug domain)",
        max_length=2000
    )
    
    @field_validator('session_id')
    @classmethod
    def validate_session_id(cls, v: str) -> str:
        """Validate session_id is non-empty"""
        v = v.strip()
        if len(v) == 0:
            raise ValueError("session_id cannot be empty")
        if not v.replace('-', '').replace('_', '').isalnum():
            raise ValueError(f"session_id must be alphanumeric (with - and _)")
        return v
    
    @field_validator('code')
    @classmethod
    def validate_code(cls, v: Optional[str]) -> Optional[str]:
        """Validate code doesn't contain dangerous patterns"""
        if v is None:
            return v
        v = v.strip()
        if len(v) == 0:
            return None
        
        # Block dangerous imports (for safety)
        dangerous = ['__import__', 'eval', 'exec', 'compile', '__loader__', '__code__']
        for danger in dangerous:
            if danger in v.lower():
                logger.warning(f"Suspicious Python pattern detected: {danger}")
                # Note: In production sandbox, you'd block this. For now, warn.
        
        return v
    
    @field_validator('review')
    @classmethod
    def validate_review(cls, v: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Validate review structure"""
        if v is None:
            return v
        if not isinstance(v, dict):
            raise ValueError("review must be a JSON object")
        
        required_fields = ['problem_identified', 'production_impact', 'fix_approach', 'fixed_code']
        missing = [f for f in required_fields if f not in v]
        if missing:
            raise ValueError(f"review missing required fields: {missing}")
        
        for field in required_fields:
            if not isinstance(v.get(field), str) or len(str(v.get(field, '')).strip()) == 0:
                raise ValueError(f"review.{field} must be non-empty string")
        
        return v


class HealthCheckResponseV2(BaseModel):
    """Enhanced Health Check Response"""
    status: Literal["ok", "degraded", "error"] = Field(..., description="Service status")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="UTC timestamp")
    active_sessions: int = Field(..., description="Active session count")
    uptime_seconds: float = Field(..., description="Uptime in seconds")
    memory_usage_mb: float = Field(..., description="Memory usage in MB")
    error_count_last_minute: int = Field(default=0, description="Errors in last 60 seconds")
    request_count_last_minute: int = Field(default=0, description="Requests in last 60 seconds")
    version: str = Field("3.0.0", description="API version")
    spec: str = Field("openenv/v1", description="OpenEnv spec version")


class ErrorResponseV2(BaseModel):
    """Standardized error response"""
    error: str = Field(..., description="Error message")
    error_code: str = Field(..., description="Machine-readable error code")
    details: Optional[str] = Field(None, description="Optional debug details")
    request_id: str = Field(..., description="Unique request ID for tracing")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="When error occurred")
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": "Session not found",
                "error_code": "SESSION_NOT_FOUND",
                "details": "Session c0a1b2c3-d4e5-f6g7-h8i9-j0k1l2m3n4o5 does not exist in session store",
                "request_id": "req-2024-04-07-14-56-23-abc123",
                "timestamp": "2024-04-07T14:56:23.123456Z"
            }
        }


# ============================================================================
# RESPONSE MODELS - Structured & Safe
# ============================================================================

class PipelineObservationV2(BaseModel):
    """Enhanced Observation with all domains"""
    task_id: str = Field(..., description="Unique task ID")
    domain: Literal["data_pipeline", "code_review", "incident_debug"] = Field(
        ..., description="Domain"
    )
    task_type: Literal["solve", "review", "debug"] = Field(
        ..., description="Task mode"
    )
    difficulty: Literal["easy", "medium", "hard"] = Field(..., description="Difficulty")
    title: str = Field(..., description="Task title")
    description: str = Field(..., description="Detailed description")
    
    # Optional domain-specific fields
    function_signature: Optional[str] = Field(None, description="Required function signature")
    data_sample: Optional[Dict[str, Any]] = Field(None, description="Sample data for pipeline domain")
    current_code: Optional[str] = Field(None, description="Broken code for review/debug")
    error_message: Optional[str] = Field(None, description="Crash message for debug tasks")
    incident_report: Optional[str] = Field(None, description="Incident description for debug domain")
    
    # Status fields
    passed_cases: int = Field(..., ge=0, description="Number of passed test cases")
    total_cases: int = Field(..., ge=0, description="Total test cases")
    step_count: int = Field(..., ge=0, description="Steps taken so far")
    max_steps: int = Field(..., ge=1, description="Max steps allowed")
    feedback: Optional[str] = Field(None, description="Progress feedback from last step")


class ResetResponseV2(BaseModel):
    """Enhanced Reset Response"""
    session_id: str = Field(..., description="Session ID for use in /step")
    observation: PipelineObservationV2 = Field(..., description="Initial task observation")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "observation": {
                    "task_id": "easy-solve-001",
                    "domain": "data_pipeline",
                    "task_type": "solve",
                    "difficulty": "easy",
                    "title": "Sales Aggregator",
                    "description": "Sum sales by customer_id",
                    "passed_cases": 0,
                    "total_cases": 8
                },
                "timestamp": "2024-04-07T14:56:23.123456Z"
            }
        }


class StepResponseV2(BaseModel):
    """Enhanced Step Response - Always has observation, reward, done, info"""
    session_id: str = Field(..., description="Session ID")
    observation: PipelineObservationV2 = Field(..., description="Updated task observation")
    reward: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Reward [0.0, 1.0] for this step"
    )
    done: bool = Field(..., description="Is episode finished (terminal state)?")
    truncated: bool = Field(default=False, description="Was episode truncated (max steps)?")
    info: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional info: reward_breakdown, test_results, etc."
    )
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "observation": {
                    "task_id": "easy-solve-001",
                    "domain": "data_pipeline",
                    "passed_cases": 5,
                    "total_cases": 8,
                    "step_count": 1
                },
                "reward": 0.625,
                "done": False,
                "truncated": False,
                "info": {
                    "reward_breakdown": {
                        "visible": 0.5,
                        "hidden": 0.125
                    },
                    "tests_passed": 5,
                    "tests_total": 8
                },
                "timestamp": "2024-04-07T14:56:24.123456Z"
            }
        }


class SessionStateV2(BaseModel):
    """Enhanced Session State Response"""
    session_id: str = Field(..., description="Session ID")
    domain: Literal["data_pipeline", "code_review", "incident_debug"] = Field(..., description="Domain")
    task_type: Literal["solve", "review", "debug"] = Field(..., description="Task mode")
    difficulty: Literal["easy", "medium", "hard"] = Field(..., description="Difficulty")
    current_step: int = Field(..., description="Current step in episode")
    max_steps: int = Field(..., description="Max steps allowed")
    cumulative_reward: float = Field(..., description="Total reward accumulated so far")
    is_terminal: bool = Field(..., description="Is episode finished?")
    created_at: datetime = Field(..., description="When session created")
    last_action_at: datetime = Field(..., description="When last action taken")
    observation: PipelineObservationV2 = Field(..., description="Current observation")


# ============================================================================
# UTILITY: Request ID Generation
# ============================================================================

def generate_request_id() -> str:
    """Generate unique request ID for tracing"""
    from datetime import datetime
    import uuid
    ts = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    uid = str(uuid.uuid4())[:8]
    return f"req-{ts}-{uid}"
