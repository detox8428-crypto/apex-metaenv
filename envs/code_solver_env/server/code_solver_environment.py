"""Code Solver Environment - Multi-session implementation with sandboxed execution"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import uuid
import asyncio
import logging
import random
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple
from asyncio import Lock

from models import (
    CodeAction, ProblemObservation, TestCaseResult, 
    EnvState, StepResponse, ResetResponse
)
from .sandbox import execute_code_sandboxed
from .rewards import RewardCalculator
from .problems import (
    CANONICAL_PROBLEMS, get_random_canonical_problem,
    get_canonical_problem, get_problem_by_id,
    ProceduralProblemGenerator, get_problems_by_difficulty
)

logger = logging.getLogger(__name__)


class SessionManager:
    """Manages multiple concurrent sessions with automatic cleanup"""

    def __init__(self, session_timeout_minutes: int = 30):
        """
        Initialize the session manager.
        
        Args:
            session_timeout_minutes: Sessions expire after this many minutes of inactivity
        """
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.session_timeout = timedelta(minutes=session_timeout_minutes)
        self.lock = Lock()
        self.leaderboard: Dict[str, list] = {}  # problem_id -> [(reward, session_id, timestamp)]

    async def create_session(self) -> str:
        """
        Create a new session.
        
        Returns:
            Session ID (UUID v4)
        """
        session_id = str(uuid.uuid4())
        async with self.lock:
            self.sessions[session_id] = {
                "created_at": datetime.utcnow(),
                "last_activity": datetime.utcnow(),
                "problem_id": None,
                "problem": None,
                "step_count": 0,
                "max_steps": 10,
                "best_reward": 0.0,
                "episode_history": [],
                "problem_source": None,
            }
        logger.debug(f"Created session {session_id}")
        return session_id

    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data, return None if not found or expired"""
        async with self.lock:
            if session_id not in self.sessions:
                return None

            session = self.sessions[session_id]
            age = datetime.utcnow() - session["last_activity"]

            if age > self.session_timeout:
                del self.sessions[session_id]
                logger.debug(f"Session {session_id} expired after {age}")
                return None

            # Update last activity
            session["last_activity"] = datetime.utcnow()
            return session

    async def delete_session(self, session_id: str) -> bool:
        """Delete a session explicitly"""
        async with self.lock:
            if session_id in self.sessions:
                del self.sessions[session_id]
                logger.debug(f"Deleted session {session_id}")
                return True
        return False

    async def get_active_sessions(self) -> list:
        """Get list of active sessions with their info"""
        async with self.lock:
            sessions_list = []
            now = datetime.utcnow()
            expired = []

            for sid, session in self.sessions.items():
                age = now - session["last_activity"]
                if age > self.session_timeout:
                    expired.append(sid)
                else:
                    sessions_list.append({
                        "session_id": sid,
                        "problem_id": session.get("problem_id"),
                        "step_count": session.get("step_count"),
                        "age_seconds": int(age.total_seconds()),
                        "best_reward": session.get("best_reward"),
                    })

            # Clean up expired sessions
            for sid in expired:
                del self.sessions[sid]

            return sessions_list

    async def record_leaderboard(self, problem_id: str, reward: float, session_id: str):
        """Record a score on the leaderboard"""
        async with self.lock:
            if problem_id not in self.leaderboard:
                self.leaderboard[problem_id] = []

            self.leaderboard[problem_id].append({
                "reward": reward,
                "session_id": session_id,
                "timestamp": datetime.utcnow()
            })

            # Keep only top 10
            self.leaderboard[problem_id].sort(
                key=lambda x: x["reward"],
                reverse=True
            )
            self.leaderboard[problem_id] = self.leaderboard[problem_id][:10]

    def get_leaderboard(self, problem_id: Optional[str] = None) -> list:
        """Get leaderboard entries"""
        if problem_id:
            entries = self.leaderboard.get(problem_id, [])
        else:
            entries = []
            for scores in self.leaderboard.values():
                entries.extend(scores)
            entries.sort(key=lambda x: x["reward"], reverse=True)

        return entries[:10]


class CodeSolverEnvironment:
    """Multi-session RL Environment for solving coding problems"""

    def __init__(self):
        """Initialize the environment"""
        self.session_manager = SessionManager()
        self.max_steps = 10

    async def reset(
        self,
        session_id: Optional[str] = None,
        difficulty: Optional[str] = None,
        mode: str = "mixed",  # canonical, procedural, mixed
        seed: Optional[int] = None
    ) -> Tuple[str, ProblemObservation]:
        """
        Reset environment and select a problem.
        
        Args:
            session_id: If provided, reuse session; otherwise create new
            difficulty: Filter by difficulty (easy/medium/hard)
            mode: Problem source (canonical, procedural, mixed)
            seed: Seed for procedural generation (if None, random)
            
        Returns:
            (session_id, observation)
        """
        # Create or get session
        if session_id:
            session = await self.session_manager.get_session(session_id)
            if not session:
                # Session expired, create new one
                session_id = await self.session_manager.create_session()
                session = await self.session_manager.get_session(session_id)
        else:
            session_id = await self.session_manager.create_session()
            session = await self.session_manager.get_session(session_id)

        # Select problem based on mode
        if mode == "procedural":
            if seed is None:
                seed = random.randint(0, 2**31 - 1)
            gen = ProceduralProblemGenerator(seed=seed)
            problem = gen.generate(
                random.choice(["two_sum", "palindrome", "sorting"]),
                difficulty or "easy"
            )
            source = "procedural"
        elif mode == "canonical":
            problem = get_random_canonical_problem(difficulty) or get_random_canonical_problem()
            source = "canonical"
        else:  # mixed
            if random.choice([True, False]):
                if seed is None:
                    seed = random.randint(0, 2**31 - 1)
                gen = ProceduralProblemGenerator(seed=seed)
                problem = gen.generate(
                    random.choice(["two_sum", "palindrome"]),
                    difficulty or "easy"
                )
                source = "procedural"
            else:
                problem = get_random_canonical_problem(difficulty) or get_random_canonical_problem()
                source = "canonical"

        # Update session
        async with self.session_manager.lock:
            session["problem_id"] = problem["problem_id"]
            session["problem"] = problem
            session["step_count"] = 0
            session["best_reward"] = 0.0
            session["episode_history"] = []
            session["problem_source"] = source
            session["max_steps"] = self.max_steps

        # Create observation
        observation = self._problem_to_observation(
            problem, 0, self.max_steps, passed_cases=0, total_cases=len(problem["test_cases"])
        )

        return session_id, observation

    async def step(
        self,
        session_id: str,
        code: str
    ) -> Tuple[ProblemObservation, float, bool, bool, Dict[str, Any]]:
        """
        Execute code and return results.
        
        Args:
            session_id: Session identifier
            code: Solution code to execute
            
        Returns:
            (observation, reward, terminated, truncated, info)
        """
        # Get session
        session = await self.session_manager.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found (may have expired)")

        problem = session.get("problem")
        if not problem:
            raise ValueError("Environment not reset - no problem loaded")

        # Increment step count
        async with self.session_manager.lock:
            session["step_count"] += 1
            step_count = session["step_count"]

        # Parse function name from signature
        func_sig = problem["function_signature"]
        func_name = func_sig.split("(")[0].replace("def ", "").strip()

        # Execute code in sandbox
        exec_result = execute_code_sandboxed(
            code=code,
            test_cases=problem["test_cases"],
            func_name=func_name,
            timeout=10
        )

        # Convert sandbox results to our model
        test_results = []
        if exec_result.get("results"):
            for result in exec_result["results"]:
                test_results.append(
                    TestCaseResult(
                        case_index=result.get("case_index", 0),
                        passed=result.get("passed", False),
                        error=result.get("error"),
                        time_ms=result.get("time_ms")
                    )
                )

        passed_cases = exec_result.get("passed_count", 0)
        total_cases = len(problem["test_cases"])
        error_type = exec_result.get("error_type")
        error_message = exec_result.get("error")

        # Calculate reward
        time_ms_total = sum(r.time_ms or 0 for r in test_results)
        code_lines = len(code.strip().split('\n'))

        reward_dict = RewardCalculator.calculate(
            passed_cases=passed_cases,
            total_cases=total_cases,
            time_ms_total=time_ms_total,
            step_count=step_count,
            code_lines=code_lines,
            error_type=error_type,
            error_message=error_message,
            test_results=[
                {
                    "case_index": r.case_index,
                    "passed": r.passed,
                    "error": r.error,
                    "time_ms": r.time_ms
                }
                for r in test_results
            ]
        )

        final_reward = reward_dict["final_reward"]

        # Update session
        async with self.session_manager.lock:
            session["episode_history"].append(final_reward)
            if final_reward > session["best_reward"]:
                session["best_reward"] = final_reward

        # Update leaderboard if solved
        if passed_cases == total_cases:
            await self.session_manager.record_leaderboard(
                problem["problem_id"],
                final_reward,
                session_id
            )

        # Determine termination
        terminated = (passed_cases == total_cases)  # All tests passed
        truncated = (step_count >= self.max_steps) and not terminated  # Max steps reached

        # Create observation
        observation = self._problem_to_observation(
            problem, step_count, self.max_steps,
            passed_cases=passed_cases,
            total_cases=total_cases,
            test_results=test_results,
            error_message=error_message
        )

        # Build info dict
        info = {
            "passed_cases": passed_cases,
            "total_cases": total_cases,
            "primary_reward": reward_dict["primary_reward"],
            "efficiency_bonus": reward_dict["efficiency_bonus"],
            "attempt_penalty": reward_dict["attempt_penalty"],
            "final_reward": final_reward,
            "per_test_results": reward_dict["per_test_results"],
            "error_type": error_type,
            "error_message": error_message,
            "time_ms_total": reward_dict["time_ms_total"],
            "code_lines": code_lines,
            "best_reward_this_episode": session["best_reward"],
        }

        return observation, final_reward, terminated, truncated, info

    async def get_state(self, session_id: str) -> EnvState:
        """Get the current state of a session"""
        session = await self.session_manager.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        return EnvState(
            session_id=session_id,
            problem_id=session.get("problem_id", ""),
            step_count=session.get("step_count", 0),
            max_steps=session.get("max_steps", self.max_steps),
            best_reward=session.get("best_reward", 0.0),
            episode_history=session.get("episode_history", []),
            created_at=session.get("created_at", datetime.utcnow()),
            last_activity=session.get("last_activity", datetime.utcnow()),
            problem_source=session.get("problem_source", "canonical")
        )

    def _problem_to_observation(
        self,
        problem: Dict[str, Any],
        step_count: int,
        max_steps: int,
        passed_cases: int = 0,
        total_cases: int = 0,
        test_results: list = None,
        error_message: str = None
    ) -> ProblemObservation:
        """Convert problem dict to ProblemObservation model"""
        if test_results is None:
            test_results = []

        return ProblemObservation(
            problem_id=problem["problem_id"],
            title=problem["title"],
            description=problem["description"],
            function_signature=problem["function_signature"],
            examples=problem["examples"],
            constraints=problem["constraints"],
            difficulty=problem["difficulty"],
            test_results=test_results,
            passed_cases=passed_cases,
            total_cases=total_cases or len(problem["test_cases"]),
            error_message=error_message,
            step_count=step_count,
            max_steps=max_steps
        )
            user_code: Agent's solution code
            func_sig: Function signature
            test_input: Input dict
            expected: Expected output
            
        Returns:
            Python script string to execute
        """
        # Extract function name from signature
        func_name = func_sig.split("(")[0].replace("def ", "").strip()

        # Build argument list
        arg_names = list(test_input.keys())
        args_str = ", ".join(arg_names)
        args_values = ", ".join(repr(test_input[name]) for name in arg_names)

        # Create test script
        script = f"""
import json
import sys

# User code
{user_code}

# Run test
try:
    result = {func_name}({args_values})
    if result == {repr(expected)}:
        print(json.dumps(result))
        sys.exit(0)
    else:
        sys.exit(1)
except Exception as e:
    print(f"Error: {{e}}", file=sys.stderr)
    sys.exit(1)
"""
        return script

    def _create_error_observation(self, error_msg: str) -> CodeSolverObservation:
        """Create an error observation"""
        return CodeSolverObservation(
            problem_id="",
            title="",
            description="",
            function_signature="",
            examples="",
            constraints="",
            difficulty="",
            test_results="",
            passed_cases=0,
            total_cases=0,
            error_message=error_msg
        )

    @property
    def state(self) -> CodeSolverState:
        """Get current state"""
        return self._state
