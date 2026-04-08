"""
APEX Engineering Benchmark - Core Environment
Manages sessions, resets, and steps
"""

import uuid
import json
import os
from typing import Dict, Tuple, Any, Optional
from models import Observation, RewardInfo
from tasks import get_task, TASKS
from graders import DataPipelineGrader, CodeReviewGrader, IncidentDebugGrader


# File-based session storage to support multiple workers on HF Spaces
SESSION_DIR = "/tmp/apex_sessions"
os.makedirs(SESSION_DIR, exist_ok=True)


class APEXEnvironment:
    """Core APEX environment - manages sessions and episodes"""
    
    def __init__(self):
        self.graders = {
            "data_pipeline": DataPipelineGrader(),
            "code_review": CodeReviewGrader(),
            "incident_debug": IncidentDebugGrader(),
        }
    
    def _save_session(self, session_id: str, data: Dict[str, Any]) -> None:
        """Save session data to JSON file"""
        path = os.path.join(SESSION_DIR, f"{session_id}.json")
        with open(path, 'w') as f:
            json.dump(data, f, default=str)
    
    def _load_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Load session data from JSON file"""
        path = os.path.join(SESSION_DIR, f"{session_id}.json")
        if not os.path.exists(path):
            return None
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except Exception:
            return None
    
    def _delete_session(self, session_id: str) -> None:
        """Delete session file"""
        path = os.path.join(SESSION_DIR, f"{session_id}.json")
        if os.path.exists(path):
            os.remove(path)
    
    def reset(self, domain: str, difficulty: str, mode: str = "solve") -> Tuple[str, Observation]:
        """
        Reset environment and start new episode.
        
        Returns:
            (session_id, observation)
        """
        # Validate inputs
        if domain not in TASKS:
            domain = "data_pipeline"
        if difficulty not in ["easy", "medium", "hard"]:
            difficulty = "easy"
        
        # Generate session ID
        session_id = str(uuid.uuid4())
        
        # Get task
        task = get_task(domain, difficulty)
        if not task:
            task = get_task(domain, "easy")
        
        # Create session state
        session_data = {
            "session_id": session_id,
            "domain": domain,
            "difficulty": difficulty,
            "mode": mode,
            "task": task,
            "step": 0,
            "rewards": [],
            "step_scores": [],
            "done": False,
            "history": []
        }
        
        # Save session to file
        self._save_session(session_id, session_data)
        
        # Create observation
        observation = Observation(
            session_id=session_id,
            task_id=task.get("task_id", "unknown"),
            domain=domain,
            difficulty=difficulty,
            title=task.get("title", ""),
            description=task.get("description", ""),
            data_sample=task.get("data_sample"),
            code_to_review=task.get("code_to_review"),
            incident_log=task.get("incident_log"),
            step_number=0,
            max_steps=task.get("max_steps", 3),
            passed_cases=0,
            total_cases=len(task.get("test_cases", [])) if domain == "data_pipeline" else 0,
            feedback=None,
            context={"domain": domain, "difficulty": difficulty}
        )
        
        return session_id, observation
    
    def step(self, session_id: str, code: str = None,
             review: str = None, diagnosis: str = None) -> Tuple[Observation, float, bool, Dict[str, Any]]:
        """
        Execute one step in episode.
        
        Returns:
            (observation, reward, done, info)
        """
        # Load session from file
        session = self._load_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        task = session["task"]
        domain = session["domain"]
        step_num = session["step"] + 1
        
        # Grade submission based on domain
        if domain == "data_pipeline":
            reward_info = self.graders["data_pipeline"].grade(code or "", task, step_num)
        elif domain == "code_review":
            reward_info = self.graders["code_review"].grade(review or "", task, step_num)
        elif domain == "incident_debug":
            reward_info = self.graders["incident_debug"].grade(
                diagnosis or "", task, step_num, session.get("step_scores", [])
            )
        else:
            # Fallback
            reward_info = RewardInfo(
                session_id=session_id,
                task_id=task.get("task_id", "unknown"),
                reward=0.0,
                done=False,
                observation=Observation(
                    session_id=session_id,
                    task_id=task.get("task_id", "unknown"),
                    domain=domain,
                    difficulty=session.get("difficulty", "easy"),
                    title="Error",
                    description="Unknown domain",
                ),
                feedback="Unknown domain",
                info={}
            )
        
        # Update session
        session["step"] = step_num
        session["rewards"].append(reward_info.reward)
        session["step_scores"] = reward_info.step_scores or [reward_info.reward]
        
        # Check if done
        done = reward_info.done or step_num >= task.get("max_steps", 3)
        session["done"] = done
        
        # Store in history
        session["history"].append({
            "step": step_num,
            "reward": reward_info.reward,
            "action": code or review or diagnosis,
            "feedback": reward_info.feedback
        })
        
        # Save session back to file
        self._save_session(session_id, session)
        
        # Update observation with step info
        obs = reward_info.observation
        obs.session_id = session_id
        obs.step_number = step_num
        obs.max_steps = task.get("max_steps", 3)
        obs.passed_cases = reward_info.passed_cases or 0
        obs.total_cases = reward_info.total_cases or 0
        obs.feedback = reward_info.feedback
        
        # Build info dict
        info = {
            "step": step_num,
            "reward": reward_info.reward,
            "done": done,
            "rewards": session["rewards"],
            "feedback": reward_info.feedback,
            "passed_cases": reward_info.passed_cases,
            "total_cases": reward_info.total_cases,
        }
        if reward_info.production_keywords_found:
            info["keywords_found"] = reward_info.production_keywords_found
        if reward_info.step_scores:
            info["step_scores"] = reward_info.step_scores
        
        return obs, reward_info.reward, done, info
    
    def state(self, session_id: str) -> Dict[str, Any]:
        """Get current session state"""
        session = self._load_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        task = session.get("task", {})
        
        return {
            "session_id": session_id,
            "domain": session.get("domain"),
            "difficulty": session.get("difficulty"),
            "task_id": task.get("task_id"),
            "step": session.get("step", 0),
            "max_steps": task.get("max_steps", 3),
            "rewards": session.get("rewards", []),
            "done": session.get("done", False),
            "history": session.get("history", [])
        }
    
    def close_session(self, session_id: str) -> None:
        """Close a session"""
        self._delete_session(session_id)
