"""
Base task class for APEXEnv
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List
from apex_env.state import APEXEnvState


@dataclass
class TaskDefinition:
    """Task metadata"""
    task_id: int
    name: str
    description: str
    difficulty: str  # "easy", "medium", "hard"
    instructions: str
    expected_actions: List[str]  # Expected action sequence
    max_steps: int
    created_at: datetime = field(default_factory=datetime.utcnow)


class BaseTask(ABC):
    """
    Abstract base class for all APEXEnv tasks.
    
    Tasks define goals for the agent to complete.
    Graders evaluate task completion.
    """

    def __init__(self, task_def: TaskDefinition):
        """Initialize task with definition"""
        self.task_def = task_def
        self.started_at = datetime.utcnow()
        self.completed_at: Optional[datetime] = None
        self.is_complete = False
        self.steps_taken = 0
        self.actions_taken: List[tuple] = []  # (step, action_type, success)

    @abstractmethod
    def get_instruction(self) -> str:
        """
        Return human-readable instruction for agent.
        Can be task description or specific guidance.
        """
        pass

    @abstractmethod
    def evaluate(self, state: APEXEnvState) -> float:
        """
        Evaluate task completion.
        
        Args:
            state: Current environment state
            
        Returns:
            Score [0.0, 1.0] indicating task success
            1.0 = perfect completion
            0.0 = no progress
        """
        pass

    @abstractmethod
    def is_success(self, state: APEXEnvState) -> bool:
        """
        Determine if task has been completed successfully.
        
        Returns:
            True if task goals achieved
        """
        pass

    def record_action(self, action_type: str, success: bool) -> None:
        """Record action taken in task"""
        self.steps_taken += 1
        self.actions_taken.append((self.steps_taken, action_type, success))

    def mark_complete(self) -> None:
        """Mark task as completed"""
        self.is_complete = True
        self.completed_at = datetime.utcnow()

    def get_duration(self) -> float:
        """Get task execution time in seconds"""
        end_time = self.completed_at or datetime.utcnow()
        return (end_time - self.started_at).total_seconds()

    def to_dict(self) -> Dict[str, Any]:
        """Serialize task to dict"""
        return {
            "task_id": self.task_def.task_id,
            "name": self.task_def.name,
            "description": self.task_def.description,
            "difficulty": self.task_def.difficulty,
            "is_complete": self.is_complete,
            "steps_taken": self.steps_taken,
            "duration_seconds": self.get_duration(),
            "actions": len(self.actions_taken),
        }
