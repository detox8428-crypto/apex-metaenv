"""HTTP Client for Screen Task Environment using OpenEnv HTTPEnvClient"""

from typing import Dict, Any
from openenv.core.http_env_client import HTTPEnvClient
from .models import ScreenAction, ScreenObservation, ScreenState


class ScreenTaskEnv(HTTPEnvClient):
    """
    OpenEnv-compatible HTTP client for Screen Task Environment.
    Uses WebSocket under the hood via HTTPEnvClient base class.
    """

    def __init__(self, server_url: str = "http://localhost:8000"):
        """
        Initialize the client
        
        Args:
            server_url: Base URL of the environment server
        """
        super().__init__(server_url)

    def _step_payload(self, action: ScreenAction) -> Dict[str, Any]:
        """
        Convert ScreenAction to step payload dict
        
        Args:
            action: ScreenAction to serialize
            
        Returns:
            Dictionary with action fields for server
        """
        return {
            "action_type": action.action_type,
            "x": action.x,
            "y": action.y,
            "text": action.text,
            "keys": action.keys
        }

    def _parse_result(self, payload: Dict[str, Any]) -> ScreenObservation:
        """
        Parse server step response into ScreenObservation
        
        Args:
            payload: Response payload from /step endpoint
            
        Returns:
            ScreenObservation object
        """
        obs_data = payload.get("observation", {})
        
        return ScreenObservation(
            screenshot_b64=obs_data.get("screenshot_b64", ""),
            task=obs_data.get("task", ""),
            last_action_result=obs_data.get("last_action_result", ""),
            step_num=obs_data.get("step_num", 0)
        )

    def _parse_state(self, payload: Dict[str, Any]) -> ScreenState:
        """
        Parse server state response into ScreenState
        
        Args:
            payload: Response payload from /state endpoint
            
        Returns:
            ScreenState object
        """
        state_data = payload.get("state", {})
        
        return ScreenState(
            task_id=state_data.get("task_id", ""),
            task_description=state_data.get("task_description", ""),
            app_handle=state_data.get("app_handle"),
            is_running=state_data.get("is_running", False)
        )


# For backward compatibility
ScreenTaskEnvClient = ScreenTaskEnv
