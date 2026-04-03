"""Data models for Screen Task Environment using OpenEnv base classes"""

from typing import Optional
from pydantic import BaseModel, Field


class ScreenAction(BaseModel):
    """Action that an agent can take in the screen task environment"""
    action_type: str = Field(..., description="Type of action: 'click', 'type', 'hotkey', or 'submit'")
    x: int = Field(default=0, description="X coordinate for click action")
    y: int = Field(default=0, description="Y coordinate for click action")
    text: str = Field(default="", description="Text to type for 'type' action")
    keys: str = Field(default="", description="Keys to press for 'hotkey' action (e.g., 'ctrl+s')")


class ScreenObservation(BaseModel):
    """Observation returned by the environment"""
    screenshot_b64: str = Field(..., description="Current screenshot encoded in base64")
    task: str = Field(..., description="Natural language description of the task")
    last_action_result: str = Field(default="", description="Result/feedback from last action")
    step_num: int = Field(default=0, description="Current step number in episode")


class ScreenState(BaseModel):
    """Internal state of the environment"""
    task_id: str = Field(default="", description="ID of current task")
    task_description: str = Field(default="", description="Full description of current task")
    app_handle: Optional[int] = Field(default=None, description="Process handle of Notepad")
    is_running: bool = Field(default=False, description="Whether episode is active")
