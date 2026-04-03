"""HTTP Client for Code Solver Environment"""

from typing import Tuple
import requests
from .models import CodeSolverAction, CodeSolverObservation, CodeSolverState


class CodeSolverEnv:
    """HTTP client for Code Solver Environment"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        Initialize the client
        
        Args:
            base_url: Base URL of the environment server
        """
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()

    def reset(self, difficulty: str = None) -> CodeSolverObservation:
        """
        Reset the environment
        
        Args:
            difficulty: Optional difficulty filter (easy/medium/hard)
            
        Returns:
            Initial observation
        """
        try:
            payload = {"difficulty": difficulty} if difficulty else {}
            response = self.session.post(f"{self.base_url}/reset", json=payload)
            response.raise_for_status()
            
            data = response.json()
            obs_data = data["observation"]
            
            return CodeSolverObservation(
                problem_id=obs_data.get("problem_id", ""),
                title=obs_data.get("title", ""),
                description=obs_data.get("description", ""),
                function_signature=obs_data.get("function_signature", ""),
                examples=obs_data.get("examples", ""),
                constraints=obs_data.get("constraints", ""),
                difficulty=obs_data.get("difficulty", ""),
                test_results=obs_data.get("test_results", ""),
                passed_cases=obs_data.get("passed_cases", 0),
                total_cases=obs_data.get("total_cases", 0),
                error_message=obs_data.get("error_message", "")
            )
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Failed to reset environment: {e}")

    def step(self, action: CodeSolverAction) -> Tuple[CodeSolverObservation, float, bool]:
        """
        Submit code for testing
        
        Args:
            action: CodeSolverAction with code
            
        Returns:
            (observation, reward, done): results of code execution
        """
        try:
            payload = {"action": {"code": action.code}}
            
            response = self.session.post(
                f"{self.base_url}/step",
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            obs_data = data["observation"]
            
            observation = CodeSolverObservation(
                problem_id=obs_data.get("problem_id", ""),
                title=obs_data.get("title", ""),
                description=obs_data.get("description", ""),
                function_signature=obs_data.get("function_signature", ""),
                examples=obs_data.get("examples", ""),
                constraints=obs_data.get("constraints", ""),
                difficulty=obs_data.get("difficulty", ""),
                test_results=obs_data.get("test_results", ""),
                passed_cases=obs_data.get("passed_cases", 0),
                total_cases=obs_data.get("total_cases", 0),
                error_message=obs_data.get("error_message", "")
            )
            
            reward = data.get("reward", 0.0)
            done = data.get("done", False)
            
            return observation, reward, done
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Failed to step environment: {e}")

    def get_state(self) -> CodeSolverState:
        """
        Get current environment state
        
        Returns:
            Current CodeSolverState
        """
        try:
            response = self.session.get(f"{self.base_url}/state")
            response.raise_for_status()
            
            data = response.json()
            state_data = data["state"]
            
            return CodeSolverState(
                problem_id=state_data.get("problem_id", ""),
                difficulty=state_data.get("difficulty", ""),
                attempts=state_data.get("attempts", 0)
            )
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Failed to get state: {e}")

    def sync(self):
        """Return self for context manager compatibility"""
        return self

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
