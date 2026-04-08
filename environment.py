"""
APEX Engineering Benchmark - Core Environment
Manages sessions, resets, and steps
"""

import uuid
import json
import os
import logging
from typing import Dict, Tuple, Any, Optional
from models import Observation, RewardInfo
from tasks import get_task, TASKS
from graders import DataPipelineGrader, CodeReviewGrader, IncidentDebugGrader

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# SESSION STORAGE - DUAL-LAYER (MEMORY + FILE)
# ============================================================================

# Memory cache for fast same-worker hits
_memory_cache = {}

# File storage for cross-worker persistence on HF Spaces
SESSION_DIR = "/tmp/apex_sessions"

# Create directory immediately when module loads
try:
    os.makedirs(SESSION_DIR, exist_ok=True)
    # Verify we can write to it
    test_path = os.path.join(SESSION_DIR, "test_write.json")
    with open(test_path, 'w') as f:
        json.dump({"test": True}, f)
    os.remove(test_path)
    logger.info(f"Session storage ready at {SESSION_DIR}")
except Exception as e:
    logger.error(f"Session storage FAILED: {e}")
    # Fallback to current directory
    SESSION_DIR = "./sessions"
    os.makedirs(SESSION_DIR, exist_ok=True)
    logger.info(f"Fallback to {SESSION_DIR}")


def save_session(session_id: str, data: dict) -> bool:
    """Save session to memory and file with atomic writes and verification"""
    try:
        # Always save to memory cache first
        _memory_cache[session_id] = data
        
        # Then save to file for cross-worker persistence
        path = os.path.join(SESSION_DIR, f"{session_id}.json")
        # Write to temp file first, then rename (atomic write)
        tmp_path = path + ".tmp"
        with open(tmp_path, 'w') as f:
            json.dump(data, f, default=str)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, path)
        # Verify it was written
        assert os.path.exists(path), f"File not found after write: {path}"
        logger.info(f"Session saved: {session_id[:8]}... at {path}")
        return True
    except Exception as e:
        logger.error(f"save_session FAILED for {session_id}: {e}")
        # Memory cache is still valid as backup
        return False


def load_session(session_id: str) -> Optional[dict]:
    """Load session from memory first, then file (for cross-worker hits)"""
    try:
        # Try memory first (same worker)
        if session_id in _memory_cache:
            logger.info(f"Session loaded from memory: {session_id[:8]}...")
            return _memory_cache[session_id]
        
        # Try file (cross-worker)
        path = os.path.join(SESSION_DIR, f"{session_id}.json")
        if not os.path.exists(path):
            # List what IS in the directory for debugging
            if os.path.exists(SESSION_DIR):
                files = os.listdir(SESSION_DIR)
                session_files = [f for f in files if f.endswith('.json')]
                logger.error(
                    f"Session {session_id[:8]}... not found. "
                    f"Dir has {len(session_files)} session files: {session_files[:5]}"
                )
            return None
        
        with open(path, 'r') as f:
            data = json.load(f)
        # Cache in memory for next access
        _memory_cache[session_id] = data
        logger.info(f"Session loaded from file: {session_id[:8]}...")
        return data
    except Exception as e:
        logger.error(f"load_session FAILED for {session_id}: {e}")
        return None


class APEXEnvironment:
    """Core APEX environment - manages sessions and episodes"""
    
    def __init__(self):
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.graders = {
            "data_pipeline": DataPipelineGrader(),
            "code_review": CodeReviewGrader(),
            "incident_debug": IncidentDebugGrader(),
        }
    
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
        
        # Store session in memory
        self.sessions[session_id] = session_data
        
        # Save to dual-layer storage (memory + file)
        saved = save_session(session_id, session_data)
        logger.info(f"Reset: session={session_id[:8]}... domain={domain} difficulty={difficulty} saved={saved}")
        
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
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")
        
        session = self.sessions[session_id]
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
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")
        
        session = self.sessions[session_id]
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
        if session_id in self.sessions:
            del self.sessions[session_id]
