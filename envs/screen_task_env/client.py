"""HTTP Client for Screen Task Environment"""

import requests
import json
from typing import Tuple
from .models import ScreenAction, ScreenObservation, ScreenState


class ScreenTaskEnvClient:
    """Synchronous HTTP client for Screen Task Environment"""

    def __init__(self, server_url: str = "http://localhost:8000"):
        """
        Initialize the client
        
        Args:
            server_url: Base URL of the environment server
        """
        self.server_url = server_url.rstrip("/")
        self.session = requests.Session()

    def reset(self) -> ScreenObservation:
        """
        Reset the environment
        
        Returns:
            Initial observation
        """
        try:
            response = self.session.post(f"{self.server_url}/reset")
            response.raise_for_status()
            
            data = response.json()
            obs_data = data["observation"]
            
            observation = ScreenObservation(
                screenshot_b64=obs_data["screenshot_b64"],
                task=obs_data["task"],
                last_action_result=obs_data["last_action_result"],
                step_num=obs_data["step_num"]
            )
            return observation
            
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Failed to reset environment: {e}")

    def step(self, action: ScreenAction) -> Tuple[ScreenObservation, float, bool]:
        """
        Execute an action in the environment
        
        Args:
            action: ScreenAction to take
            
        Returns:
            (observation, reward, done): Tuple of observation, reward, and episode end flag
        """
        try:
            payload = {
                "action": {
                    "action_type": action.action_type,
                    "x": action.x,
                    "y": action.y,
                    "text": action.text,
                    "keys": action.keys
                }
            }
            
            response = self.session.post(
                f"{self.server_url}/step",
                json=payload
            )
            response.raise_for_status()
            
            data = response.json()
            obs_data = data["observation"]
            
            observation = ScreenObservation(
                screenshot_b64=obs_data["screenshot_b64"],
                task=obs_data["task"],
                last_action_result=obs_data["last_action_result"],
                step_num=obs_data["step_num"]
            )
            
            reward = data["reward"]
            done = data["done"]
            
            return observation, reward, done
            
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Failed to step environment: {e}")

    def get_state(self) -> ScreenState:
        """
        Get current environment state
        
        Returns:
            Current ScreenState
        """
        try:
            response = self.session.get(f"{self.server_url}/state")
            response.raise_for_status()
            
            data = response.json()
            state_data = data["state"]
            
            state = ScreenState(
                task_id=state_data["task_id"],
                task_description=state_data["task_description"],
                app_handle=state_data.get("app_handle"),
                is_running=state_data["is_running"]
            )
            return state
            
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Failed to get state: {e}")

    def close(self):
        """Close the client session"""
        if self.session:
            self.session.close()

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
