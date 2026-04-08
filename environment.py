"""
APEX Engineering Benchmark - Core Environment
Manages sessions, resets, and steps
"""

import uuid
import json
import os
import logging
import sqlite3
import threading
from typing import Dict, Tuple, Any, Optional
from models import Observation, RewardInfo
from tasks import get_task, TASKS
from graders import DataPipelineGrader, CodeReviewGrader, IncidentDebugGrader

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# SESSION STORAGE - SQLite (for multi-worker HF Spaces compatibility)
# ============================================================================

# Use app root directory which is shared across all workers
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "apex_sessions.db")
_db_lock = threading.Lock()

logger.info(f"SQLite database path: {DB_PATH}")


def _get_db():
    """Get SQLite connection and ensure table exists"""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            data TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    return conn


# Initialize DB on startup
try:
    _get_db().close()
    logger.info(f"✅ SQLite session storage ready at {DB_PATH}")
except Exception as e:
    logger.error(f"❌ Failed to initialize SQLite: {e}")


def save_session(session_id: str, data: dict) -> bool:
    """Save session to SQLite (shared across all workers)"""
    try:
        with _db_lock:
            conn = _get_db()
            conn.execute(
                "INSERT OR REPLACE INTO sessions (session_id, data) VALUES (?, ?)",
                (session_id, json.dumps(data, default=str))
            )
            conn.commit()
            conn.close()
        logger.debug(f"Session saved to SQLite: {session_id[:8]}...")
        return True
    except Exception as e:
        logger.error(f"save_session failed: {e}")
        return False


def load_session(session_id: str) -> Optional[dict]:
    """Load session from SQLite"""
    try:
        conn = _get_db()
        row = conn.execute(
            "SELECT data FROM sessions WHERE session_id = ?",
            (session_id,)
        ).fetchone()
        conn.close()
        
        if row:
            logger.debug(f"Session loaded from SQLite: {session_id[:8]}...")
            return json.loads(row[0])
        
        logger.error(f"Session not found in SQLite: {session_id[:8]}...")
        return None
    except Exception as e:
        logger.error(f"load_session failed: {e}")
        return None


def delete_session(session_id: str) -> bool:
    """Delete session from SQLite"""
    try:
        with _db_lock:
            conn = _get_db()
            conn.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
            conn.commit()
            conn.close()
        logger.debug(f"Session deleted from SQLite: {session_id[:8]}...")
        return True
    except Exception as e:
        logger.error(f"delete_session failed: {e}")
        return False


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
        
        # Save to SQLite for cross-worker persistence
        save_session(session_id, {
            "session_id": session_id,
            "domain": domain,
            "difficulty": difficulty,
            "mode": mode,
            "step": 0,
            "rewards": [],
            "step_scores": [],
            "done": False,
            "history": [],
            "task_id": task.get("task_id", "unknown")
        })
        logger.info(f"Reset: session={session_id[:8]}... domain={domain} difficulty={difficulty}")
        
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
        # Try memory first, then SQLite for cross-worker support
        if session_id not in self.sessions:
            session_data = load_session(session_id)
            if not session_data:
                raise ValueError(f"Session {session_id} not found")
            # Restore to memory for this session
            self.sessions[session_id] = session_data
        
        
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
        
        # Save updated session to SQLite for cross-worker persistence
        save_session(session_id, session)
        
        return obs, reward_info.reward, done, info
    
    def state(self, session_id: str) -> Dict[str, Any]:
        """Get current session state"""
        # Try memory first, then SQLite
        if session_id not in self.sessions:
            session_data = load_session(session_id)
            if not session_data:
                raise ValueError(f"Session {session_id} not found")
            # Restore to memory
            self.sessions[session_id] = session_data
        
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
