"""
Base grader class for APEXEnv

Graders evaluate task completion and assign deterministic scores.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any
from apex_env.state import APEXEnvState


class BaseGrader(ABC):
    """
    Abstract base class for task graders.
    
    Graders evaluate task completion deterministically.
    All scoring is deterministic (same inputs → same score).
    """

    def __init__(self, grader_name: str):
        """Initialize grader"""
        self.grader_name = grader_name
        self.evaluation_count = 0
        self.evaluation_history: list = []

    @abstractmethod
    def evaluate(self, state: APEXEnvState, task_data: Dict[str, Any]) -> float:
        """
        Evaluate task completion.
        
        Args:
            state: Current environment state
            task_data: Task-specific data dict
                      (contains expected values, constraints, etc.)
        
        Returns:
            Score in range [0.0, 1.0]
            1.0 = perfect completion
            0.0 = no progress / failure
        """
        pass

    @abstractmethod
    def get_detailed_feedback(self) -> str:
        """Return human-readable feedback on last evaluation"""
        pass

    def _record_evaluation(self, score: float, details: Dict[str, Any]) -> None:
        """Record evaluation for audit trail"""
        self.evaluation_count += 1
        self.evaluation_history.append({
            "evaluation_num": self.evaluation_count,
            "timestamp": datetime.utcnow(),
            "score": score,
            "details": details,
        })

    def get_evaluation_history(self) -> list:
        """Get all evaluations performed"""
        return self.evaluation_history.copy()
