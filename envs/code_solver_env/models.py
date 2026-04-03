"""Data models for Code Solver Environment"""

from pydantic import BaseModel, Field
from typing import Optional


class CodeSolverAction(BaseModel):
    """Action: agent submits Python code to solve problem"""
    code: str = Field(..., description="Python solution code")


class CodeSolverObservation(BaseModel):
    """Observation: problem statement and test results"""
    problem_id: str = Field(..., description="Unique problem ID")
    title: str = Field(..., description="Problem title")
    description: str = Field(..., description="Problem description")
    function_signature: str = Field(..., description="Required function signature")
    examples: str = Field(..., description="Input/output examples")
    constraints: str = Field(..., description="Problem constraints")
    difficulty: str = Field(..., description="Problem difficulty: easy/medium/hard")
    test_results: str = Field(default="", description="Feedback on test execution")
    passed_cases: int = Field(default=0, description="Number of passed test cases")
    total_cases: int = Field(default=0, description="Total number of test cases")
    error_message: str = Field(default="", description="Syntax/runtime error if any")


class CodeSolverState(BaseModel):
    """Internal state of the environment"""
    problem_id: str = Field(default="", description="Current problem ID")
    difficulty: str = Field(default="", description="Current difficulty level")
    attempts: int = Field(default=0, description="Number of attempts so far")
