"""
OpenEnv Inference - LLM Agent for Screen Task Environment

This script runs an agent that:
1. Connects to the Screen Task Environment
2. Receives a task description and screenshot
3. Uses LLM (if available) or rule-based logic to decide actions
4. Executes actions (click, type, hotkey, submit)
5. Evaluates task completion

Used by hackathon dashboard for agent evaluation.
"""

import os
import sys
import time
import base64
import re
import json
import requests
from io import BytesIO
from typing import Optional

# Get environment variables (injected by dashboard)
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
MODEL_NAME = os.getenv("MODEL_NAME", "")
HF_TOKEN = os.getenv("HF_TOKEN", "")

# Import environment classes
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "envs", "screen_task_env"))
from client import ScreenTaskEnv
from models import ScreenAction


class SimpleAgent:
    """Rule-based agent for task execution"""

    def __init__(self):
        self.env = ScreenTaskEnv(API_BASE_URL)
        self.llm_endpoint = API_BASE_URL if API_BASE_URL.startswith("http") else None

    def extract_text_from_task(self, task_description: str) -> str:
        """
        Extract the target text from task description using simple heuristics
        
        Examples:
        - "Type 'Python'" -> "Python"
        - "Type the word 'Hello World'" -> "Hello World"
        - "Type 'OpenEnv Challenge'" -> "OpenEnv Challenge"
        """
        # Look for quoted strings
        # Try to find text in quotes
        match = re.search(r"['\"]([^'\"]+)['\"]", task_description)
        if match:
            return match.group(1)
        
        # Fallback: extract capital words (simple heuristic)
        words = task_description.split()
        capitals = [w for w in words if w and w[0].isupper()]
        if capitals:
            return " ".join(capitals[:2])
        
        return ""

    def get_action_from_llm(self, task_description: str, screenshot_b64: str) -> Optional[dict]:
        """
        Query LLM (if available) to decide next action
        
        Args:
            task_description: Natural language task
            screenshot_b64: Current screenshot in base64
            
        Returns:
            Dictionary with action_type, x, y, text, keys (or None if LLM not available)
        """
        if not MODEL_NAME or not API_BASE_URL:
            return None
        
        try:
            # Attempt to call HuggingFace Inference API or other LLM endpoint
            if "huggingface" in API_BASE_URL.lower() or "hf.space" in API_BASE_URL.lower():
                # HF Inference API call
                headers = {}
                if HF_TOKEN:
                    headers["Authorization"] = f"Bearer {HF_TOKEN}"
                
                prompt = f"""You are an agent controlling a computer. 
                Task: {task_description}
                
                What action should you take?
                Respond with JSON: {{"action_type": "type" or "click" or "hotkey" or "submit", "text": "...", "keys": "...", "x": 0, "y": 0}}"""
                
                response = requests.post(
                    API_BASE_URL,
                    json={"inputs": prompt, "parameters": {"max_new_tokens": 100}},
                    headers=headers,
                    timeout=5
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if isinstance(result, list) and len(result) > 0:
                        text = result[0].get("generated_text", "")
                        # Parse JSON from response
                        json_match = re.search(r"\{.*\}", text)
                        if json_match:
                            return json.loads(json_match.group())
        except Exception as e:
            print(f"LLM call failed: {e}, falling back to rule-based")
        
        return None

    def run_episode(self, max_steps: int = 10, verbose: bool = True) -> dict:
        """
        Run a single episode of the agent
        
        Args:
            max_steps: Maximum number of steps in episode
            verbose: Print progress
            
        Returns:
            Dictionary with episode statistics
        """
        # Reset environment
        if verbose:
            print("\n" + "=" * 60)
            print("RESETTING ENVIRONMENT")
            print("=" * 60)
        
        obs = self.env.reset()
        task = obs.task
        
        if verbose:
            print(f"Task: {task}")
            print(f"Step: {obs.step_num}")
        
        total_reward = 0.0
        step_count = 0
        done = False
        
        # Episode loop
        for step_idx in range(max_steps):
            if done:
                break
            
            # Decide action: try LLM first, fallback to rule-based
            action_dict = self.get_action_from_llm(task, obs.screenshot_b64)
            
            if action_dict is None:
                # Rule-based: extract text and type it
                target_text = self.extract_text_from_task(task)
                
                if target_text and step_idx == 0:
                    # First step: type the target text
                    action = ScreenAction(
                        action_type="type",
                        text=target_text
                    )
                else:
                    # Subsequent steps: submit
                    action = ScreenAction(action_type="submit")
            else:
                # Use LLM-decided action
                action = ScreenAction(
                    action_type=action_dict.get("action_type", "submit"),
                    x=action_dict.get("x", 0),
                    y=action_dict.get("y", 0),
                    text=action_dict.get("text", ""),
                    keys=action_dict.get("keys", "")
                )
            
            # Execute action
            if verbose:
                print(f"\nStep {step_idx + 1}: {action.action_type}", end="")
                if action.text:
                    print(f" (text: '{action.text}')", end="")
                if action.keys:
                    print(f" (keys: '{action.keys}')", end="")
                print()
            
            obs, reward, done = self.env.step(action)
            total_reward += reward
            step_count += 1
            
            if verbose:
                print(f"  Reward: {reward:.1f}, Done: {done}")
                if obs.last_action_result:
                    print(f"  Result: {obs.last_action_result}")
        
        # Episode summary
        success = total_reward > 0.0
        stats = {
            "task": task,
            "success": success,
            "reward": total_reward,
            "steps": step_count,
            "max_steps": max_steps
        }
        
        if verbose:
            print("\n" + "=" * 60)
            print("EPISODE COMPLETE")
            print(f"Success: {success}")
            print(f"Total Reward: {total_reward:.1f}")
            print(f"Steps: {step_count}/{max_steps}")
            print("=" * 60)
        
        return stats


def main():
    """Main entry point - run agent on environment"""
    print("OpenEnv Inference Test")
    print(f"Environment URL: {API_BASE_URL}")
    print(f"Model: {MODEL_NAME if MODEL_NAME else 'Rule-based'}")
    
    agent = SimpleAgent()
    
    try:
        stats = agent.run_episode(max_steps=10, verbose=True)
        
        # Return success code
        sys.exit(0 if stats["success"] else 1)
        
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(2)


if __name__ == "__main__":
    main()
