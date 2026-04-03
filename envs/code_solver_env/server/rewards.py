"""Reward calculation and feedback system"""

from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class RewardCalculator:
    """
    Compute multi-faceted rewards for RL training.
    
    Primary reward = passed_cases / total_cases
    Efficiency bonus = +0.1 if all tests pass in < 2s
    Attempt penalty = -0.02 * step_count
    Final reward = clip(primary + efficiency + penalty, 0.0, 1.0)
    """

    EFFICIENCY_THRESHOLD_MS = 2000.0  # 2 seconds
    EFFICIENCY_BONUS = 0.1
    ATTEMPT_PENALTY_PER_STEP = 0.02
    TIME_PATIENCE_FACTOR = 0.05  # Deduct 5% per 0.5s over threshold

    @staticmethod
    def calculate(
        passed_cases: int,
        total_cases: int,
        time_ms_total: float,
        step_count: int,
        code_lines: int,
        error_type: str = None,
        error_message: str = None,
        test_results: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Calculate reward and secondary signals.
        
        Args:
            passed_cases: Number of test cases passed
            total_cases: Total number of test cases
            time_ms_total: Total execution time in milliseconds
            step_count: Number of steps/attempts taken
            code_lines: Lines of submitted code
            error_type: Type of error if any (SYNTAX, RUNTIME, TIMEOUT, SECURITY, WRONG_ANSWER)
            error_message: Error message if any
            test_results: List of individual test case results
            
        Returns:
            Dictionary with reward breakdown:
            {
                "passed_cases": int,
                "total_cases": int,
                "primary_reward": float,      # test pass rate
                "efficiency_bonus": float,   # time-based bonus
                "attempt_penalty": float,    # penalty for multiple attempts
                "final_reward": float,       # clipped to [0, 1]
                "per_test_results": [...],   # detailed results
                "error_type": str | null,
                "error_message": str | null,
                "time_ms_total": float,
                "code_lines": int,
                "per_test_times": list[float] | null
            }
        """
        # Primary reward: fraction of tests passed
        if total_cases == 0:
            primary_reward = 0.0
        else:
            primary_reward = passed_cases / total_cases

        # Efficiency bonus: reward fast solutions
        efficiency_bonus = 0.0
        if passed_cases == total_cases:  # All tests pass
            if time_ms_total < RewardCalculator.EFFICIENCY_THRESHOLD_MS:
                efficiency_bonus = RewardCalculator.EFFICIENCY_BONUS
            else:
                # Small penalty for being slow (but still solving)
                excess_ms = time_ms_total - RewardCalculator.EFFICIENCY_THRESHOLD_MS
                efficiency_bonus = -min(0.05, excess_ms / 1000 * RewardCalculator.TIME_PATIENCE_FACTOR)

        # Attempt penalty: encourage solving in few steps
        attempt_penalty = -(step_count - 1) * RewardCalculator.ATTEMPT_PENALTY_PER_STEP

        # Final reward (clipped to [0, 1])
        final_reward = primary_reward + efficiency_bonus + attempt_penalty
        final_reward = max(0.0, min(1.0, final_reward))

        # Extract per-test timing if available
        per_test_times = None
        if test_results:
            per_test_times = [
                r.get("time_ms", 0.0) for r in test_results
            ]

        return {
            "passed_cases": passed_cases,
            "total_cases": total_cases,
            "primary_reward": round(primary_reward, 4),
            "efficiency_bonus": round(efficiency_bonus, 4),
            "attempt_penalty": round(attempt_penalty, 4),
            "final_reward": round(final_reward, 4),
            "per_test_results": test_results or [],
            "error_type": error_type,
            "error_message": error_message,
            "time_ms_total": round(time_ms_total, 2),
            "code_lines": code_lines,
            "per_test_times": per_test_times
        }

    @staticmethod
    def interpret_error_type(error_message: str = None, sandbox_error_type: str = None) -> str:
        """
        Classify error into a category.
        
        Args:
            error_message: Error message from execution
            sandbox_error_type: Error type from sandbox.execute_code_sandboxed
            
        Returns:
            Error type string: SYNTAX, RUNTIME, TIMEOUT, SECURITY, WRONG_ANSWER
        """
        if sandbox_error_type:
            if sandbox_error_type.upper() == "TIMEOUT":
                return "TIMEOUT"
            elif sandbox_error_type.upper() == "SECURITY":
                return "SECURITY"
            elif sandbox_error_type.upper() in ("RUNTIME", "EXECUTION"):
                return "RUNTIME"

        if error_message:
            msg_lower = error_message.lower()
            if "syntaxerror" in msg_lower:
                return "SYNTAX"
            elif "timeout" in msg_lower:
                return "TIMEOUT"
            elif "security" in msg_lower:
                return "SECURITY"
            else:
                return "RUNTIME"

        return "WRONG_ANSWER"
