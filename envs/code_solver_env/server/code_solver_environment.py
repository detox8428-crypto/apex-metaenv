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
    PipelineAction, PipelineObservation, TestCaseResult,
    EnvState, StepResponse, ResetResponse
)
from .sandbox import execute_code_sandboxed
from .rewards import RewardCalculator
from .problems import (
    CANONICAL_PROBLEMS, BUGGY_PROBLEMS, get_random_canonical_problem,
    get_canonical_problem, get_problem_by_id, get_random_buggy_problem,
    ProceduralProblemGenerator, get_problems_by_difficulty, get_buggy_problems_by_difficulty
)

logger = logging.getLogger(__name__)


class CurriculumLearner:
    """Tracks agent performance and recommends difficulty progression"""

    def __init__(self):
        """Initialize curriculum learner"""
        # agent_id -> {difficulty -> [rewards]}
        self.performance_history: Dict[str, Dict[str, list]] = {}
        self.agent_difficulty: Dict[str, str] = {}  # agent_id -> current recommended difficulty
        self.lock = Lock()
        # Thresholds for curriculum progression
        self.easy_threshold = 0.75  # Move to medium if easy avg > 0.75
        self.medium_threshold = 0.75  # Move to hard if medium avg > 0.75

    async def record_episode(self, agent_id: str, difficulty: str, reward: float):
        """Record an episode result for an agent"""
        async with self.lock:
            if agent_id not in self.performance_history:
                self.performance_history[agent_id] = {"easy": [], "medium": [], "hard": []}
                self.agent_difficulty[agent_id] = "easy"  # Start at easy
            
            self.performance_history[agent_id][difficulty].append(reward)
            logger.debug(f"Agent {agent_id[:8]} recorded reward {reward:.2f} on {difficulty}")

    async def get_next_difficulty(self, agent_id: str, mode: str = "solve") -> str:
        """
        Get recommended difficulty for next episode based on performance.
        
        Curriculum progression:
        - Start at easy
        - Easy avg > 0.75 → medium
        - Medium avg > 0.75 → hard
        
        Args:
            agent_id: Agent/session identifier
            mode: "solve" or "review" (curriculum applies to both)
        
        Returns:
            Recommended difficulty: "easy", "medium", or "hard"
        """
        async with self.lock:
            if agent_id not in self.performance_history:
                self.performance_history[agent_id] = {"easy": [], "medium": [], "hard": []}
                self.agent_difficulty[agent_id] = "easy"
                return "easy"

            history = self.performance_history[agent_id]
            
            # Calculate average rewards
            easy_avg = sum(history["easy"]) / len(history["easy"]) if history["easy"] else 0.0
            medium_avg = sum(history["medium"]) / len(history["medium"]) if history["medium"] else 0.0
            
            # Curriculum progression logic
            if medium_avg > self.medium_threshold:
                next_difficulty = "hard"
            elif easy_avg > self.easy_threshold:
                next_difficulty = "medium"
            else:
                next_difficulty = "easy"
            
            self.agent_difficulty[agent_id] = next_difficulty
            
            logger.info(
                f"Agent {agent_id[:8]} curriculum update: "
                f"easy_avg={easy_avg:.2f}, medium_avg={medium_avg:.2f} → {next_difficulty}"
            )
            return next_difficulty

    async def get_progress(self, agent_id: str) -> Dict[str, Any]:
        """Get detailed progress report for an agent"""
        async with self.lock:
            if agent_id not in self.performance_history:
                return {
                    "agent_id": agent_id,
                    "episodes_completed": 0,
                    "current_difficulty": "easy",
                    "easy_performance": {"episodes": 0, "avg_reward": 0.0, "max_reward": 0.0},
                    "medium_performance": {"episodes": 0, "avg_reward": 0.0, "max_reward": 0.0},
                    "hard_performance": {"episodes": 0, "avg_reward": 0.0, "max_reward": 0.0},
                }

            history = self.performance_history[agent_id]
            
            def compute_stats(rewards):
                if not rewards:
                    return {"episodes": 0, "avg_reward": 0.0, "max_reward": 0.0}
                return {
                    "episodes": len(rewards),
                    "avg_reward": sum(rewards) / len(rewards),
                    "max_reward": max(rewards)
                }

            total_episodes = sum(len(rewards) for rewards in history.values())
            
            return {
                "agent_id": agent_id,
                "episodes_completed": total_episodes,
                "current_difficulty": self.agent_difficulty.get(agent_id, "easy"),
                "easy_performance": compute_stats(history["easy"]),
                "medium_performance": compute_stats(history["medium"]),
                "hard_performance": compute_stats(history["hard"]),
                "progression_status": self._get_progression_status(agent_id, history),
            }

    def _get_progression_status(self, agent_id: str, history: Dict[str, list]) -> str:
        """Get human-readable progression status"""
        easy_avg = sum(history["easy"]) / len(history["easy"]) if history["easy"] else 0.0
        medium_avg = sum(history["medium"]) / len(history["medium"]) if history["medium"] else 0.0
        
        if medium_avg > self.medium_threshold:
            return "🏆 Mastered medium → Progressed to hard"
        elif easy_avg > self.easy_threshold:
            return "✅ Mastered easy → Progressed to medium"
        elif history["easy"]:
            return "📈 Improving on easy"
        else:
            return "🚀 Just started"



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
    """Multi-session RL Environment for solving coding problems with curriculum learning"""

    def __init__(self):
        """Initialize the environment"""
        self.session_manager = SessionManager()
        self.curriculum = CurriculumLearner()
        self.max_steps = 10

    async def reset(
        self,
        session_id: Optional[str] = None,
        difficulty: Optional[str] = None,
        mode: str = "solve",  # solve or review
        seed: Optional[int] = None,
        problem_source: str = "mixed"  # canonical, procedural, mixed
    ) -> Tuple[str, PipelineObservation]:
        """
        Reset environment and select a problem.
        
        Args:
            session_id: If provided, reuse session; otherwise create new
            difficulty: Filter by difficulty (easy/medium/hard). If None, uses curriculum learning.
            mode: Task mode (solve=write code, review=fix buggy code)
            seed: Seed for procedural generation (if None, random)
            problem_source: Problem source (canonical, procedural, mixed)
            
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

        # Curriculum learning: if difficulty not specified, use agent's current curriculum level
        if difficulty is None:
            difficulty = await self.curriculum.get_next_difficulty(session_id, mode=mode)
            logger.info(f"Session {session_id[:8]} curriculum level: {difficulty}")
        
        # Store difficulty in session for step() to use when recording progress
        async with self.session_manager.lock:
            session["current_difficulty"] = difficulty
            session["current_mode"] = mode

        # Select problem based on mode
        if mode == "review":
            # Get a buggy problem for code review
            problem = get_random_buggy_problem(difficulty) or get_random_buggy_problem()
            source = "buggy"
        else:
            # Get a canonical or procedural problem for solving
            if problem_source == "procedural":
                if seed is None:
                    seed = random.randint(0, 2**31 - 1)
                try:
                    gen = ProceduralProblemGenerator(seed=seed)
                    problem = gen.generate(
                        random.choice(["two_sum", "palindrome", "sorting"]),
                        difficulty or "easy"
                    )
                    source = "procedural"
                except Exception as e:
                    logger.error(f"Error generating procedural problem with seed {seed}: {e}", exc_info=True)
                    # Fallback to canonical problem
                    problem = get_random_canonical_problem(difficulty) or get_random_canonical_problem()
                    source = "canonical"
            elif problem_source == "canonical":
                problem = get_random_canonical_problem(difficulty) or get_random_canonical_problem()
                source = "canonical"
            else:  # mixed
                if random.choice([True, False]):
                    if seed is None:
                        seed = random.randint(0, 2**31 - 1)
                    try:
                        gen = ProceduralProblemGenerator(seed=seed)
                        problem = gen.generate(
                            random.choice(["two_sum", "palindrome"]),
                            difficulty or "easy"
                        )
                        source = "procedural"
                    except Exception as e:
                        logger.error(f"Error generating procedural problem (mixed mode) with seed {seed}: {e}", exc_info=True)
                        # Fallback to canonical
                        problem = get_random_canonical_problem(difficulty) or get_random_canonical_problem()
                        source = "canonical"
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
            session["current_mode"] = mode  # Store task mode (solve or review)

        # Create observation
        if mode == "review":
            # For review mode, include buggy code in description
            description = f"{problem['description']}\n\nThe following code has a bug. Find and fix it:\n\n{problem['buggy_code']}"
            observation = self._problem_to_observation(
                problem, 0, self.max_steps, passed_cases=0, total_cases=len(problem["test_cases"]),
                description_override=description
            )
        else:
            observation = self._problem_to_observation(
                problem, 0, self.max_steps, passed_cases=0, total_cases=len(problem["test_cases"])
            )

        return session_id, observation

    async def step(
        self,
        session_id: str,
        code: str
    ) -> Tuple[PipelineObservation, float, bool, bool, Dict[str, Any]]:
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

        current_mode = session.get("current_mode", "solve")

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

        # Calculate reward (handle review mode)
        if current_mode == "review":
            # In review mode, give partial credit for fixing the bug even if not all tests pass
            if passed_cases == total_cases:
                final_reward = 1.0  # Perfect score
            elif passed_cases >= 3:  # At least 3/5 tests pass (main bug fixed)
                final_reward = 0.5  # Partial credit - main bug fixed but may have edge case issues
            else:
                final_reward = 0.1 * passed_cases / total_cases  # Minimal credit for partial fixes
        else:
            # In solve mode, use standard reward calculation
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

        # Record episode for curriculum learning (only when episode ends)
        if terminated or truncated:
            difficulty = session.get("current_difficulty", "easy")
            await self.curriculum.record_episode(session_id, difficulty, final_reward)
            logger.info(
                f"Session {session_id[:8]} episode complete: "
                f"difficulty={difficulty}, reward={final_reward:.2f}, "
                f"terminated={terminated}"
            )

        # Create observation
        if current_mode == "review":
            description = f"{problem['description']}\n\nThe following code has a bug. Find and fix it:\n\n{problem['buggy_code']}"
            observation = self._problem_to_observation(
                problem, step_count, self.max_steps,
                passed_cases=passed_cases,
                total_cases=total_cases,
                test_results=test_results,
                error_message=error_message,
                description_override=description
            )
        else:
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
            "final_reward": final_reward,
            "error_type": error_type,
            "error_message": error_message,
            "best_reward_this_episode": session["best_reward"],
            "mode": current_mode,
        }

        if current_mode == "solve":
            info.update({
                "primary_reward": reward_dict.get("primary_reward", 0),
                "efficiency_bonus": reward_dict.get("efficiency_bonus", 0),
                "attempt_penalty": reward_dict.get("attempt_penalty", 0),
                "per_test_results": reward_dict.get("per_test_results", []),
                "time_ms_total": reward_dict.get("time_ms_total", 0),
                "code_lines": len(code.strip().split('\n')),
                "reward_breakdown": reward_dict.get("reward_breakdown", {}),  # Rich reward signals
            })

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
        error_message: str = None,
        description_override: str = None
    ) -> PipelineObservation:
        """Convert problem dict to ProblemObservation model"""
        if test_results is None:
            test_results = []

        # Use override description if provided (for review mode)
        description = description_override if description_override else problem["description"]

        return PipelineObservation(
            problem_id=problem["problem_id"],
            title=problem["title"],
            description=description,
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

    def _create_error_observation(self, error_msg: str) -> PipelineObservation:
        """Create an error observation"""
        return PipelineObservation(
            problem_id="error",
            title="Error",
            description=error_msg,
            function_signature="",
            examples="",
            constraints="",
            difficulty="easy",
            test_results=[],
            passed_cases=0,
            total_cases=0,
            error_message=error_msg
        )

    @property
    def state(self) -> EnvState:
        """Get current state"""
        return self._state
