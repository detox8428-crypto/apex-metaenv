"""
APEX Engineering Benchmark - Pydantic v2 Models
Type-safe request/response models for OpenEnv spec
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any, List
from enum import Enum


class Domain(str, Enum):
    """Engineering domains"""
    DATA_PIPELINE = "data_pipeline"
    CODE_REVIEW = "code_review"
    INCIDENT_DEBUG = "incident_debug"


class Difficulty(str, Enum):
    """Difficulty levels"""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class Observation(BaseModel):
    """Environment observation - returned by reset() and step()"""
    session_id: str = Field(..., description="Unique session ID")
    task_id: str = Field(..., description="Task identifier")
    domain: str = Field(..., description="Engineering domain")
    difficulty: str = Field(..., description="Easy/medium/hard")
    title: str = Field(..., description="Task title")
    description: str = Field(..., description="Detailed task description")
    data_sample: Optional[str] = Field(None, description="Sample data (for data_pipeline)")
    code_to_review: Optional[str] = Field(None, description="Code to review (for code_review)")
    incident_log: Optional[str] = Field(None, description="Incident log (for incident_debug)")
    step_number: int = Field(0, description="Current step in episode")
    max_steps: int = Field(3, description="Maximum steps allowed")
    passed_cases: int = Field(0, description="Test cases passed so far")
    total_cases: int = Field(0, description="Total test cases")
    feedback: Optional[str] = Field(None, description="Feedback from previous step")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")


class Action(BaseModel):
    """Agent action - sent in step() request"""
    session_id: str = Field(..., description="Session ID from reset()")
    code: Optional[str] = Field(None, description="Python code submission (data_pipeline/incident_debug)")
    review: Optional[str] = Field(None, description="Code review text (code_review)")
    diagnosis: Optional[str] = Field(None, description="Incident diagnosis (incident_debug)")


class RewardInfo(BaseModel):
    """Reward information - returned by step()"""
    session_id: str
    task_id: str
    reward: float = Field(..., ge=0.02, le=0.98, description="Reward (0, 1)")
    done: bool = Field(..., description="Is episode finished?")
    observation: Observation = Field(..., description="Updated observation")
    passed_cases: Optional[int] = Field(None, description="Test cases passed")
    total_cases: Optional[int] = Field(None, description="Total test cases")
    production_keywords_found: Optional[List[str]] = Field(None, description="Keywords found (code_review)")
    step_scores: Optional[List[float]] = Field(None, description="Per-step scores (incident_debug)")
    feedback: str = Field(..., description="Human-readable feedback")
    info: Dict[str, Any] = Field(default_factory=dict, description="Additional info")

    @field_validator('step_scores', mode='before')
    @classmethod
    def validate_step_scores(cls, v):
        """Ensure all step_scores elements are within [0.02, 0.98]"""
        if v is None:
            return v
        if not isinstance(v, list):
            raise ValueError('step_scores must be a list or None')
        for i, score in enumerate(v):
            if not isinstance(score, (int, float)):
                raise ValueError(f'step_scores[{i}] must be numeric, got {type(score).__name__}')
            if score < 0.02 or score > 0.98:
                raise ValueError(f'step_scores[{i}]={score} must be in [0.02, 0.98]')
        return v


class ResetRequest(BaseModel):
    """Reset request body"""
    task: Optional[str] = Field(None, description="Direct task ID lookup (e.g., 'easy-solve-001')")
    domain: Optional[str] = Field(None, description="data_pipeline, code_review, or incident_debug")
    difficulty: Optional[str] = Field(None, description="easy, medium, or hard")
    mode: str = Field(default="solve", description="solve or review")


class ResetResponse(BaseModel):
    """Reset response body"""
    session_id: str
    observation: Observation


class StepRequest(BaseModel):
    """Step request body"""
    session_id: str
    code: Optional[str] = None
    review: Optional[str] = None
    diagnosis: Optional[str] = None


class StepResponse(BaseModel):
    """Step response body"""
    session_id: str
    observation: Observation
    reward: float
    done: bool
    passed_cases: Optional[int] = None
    total_cases: Optional[int] = None
    feedback: str
    info: Dict[str, Any] = Field(default_factory=dict)
