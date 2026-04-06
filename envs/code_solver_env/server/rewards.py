"""Reward calculation and feedback system with rich RL signals"""

from typing import Dict, Any, List, Optional
import logging
import re

logger = logging.getLogger(__name__)


class RewardCalculator:
    """
    Compute multi-faceted rewards for RL training with rich signals:
    
    - Test pass rate (primary)
    - Efficiency bonus (fast execution)
    - Complexity penalty (detects O(n²) vs O(n))
    - Code quality bonus (elegant, short solutions)
    - Improvement bonus (learning from feedback)
    - Detailed breakdown for agent learning
    """

    EFFICIENCY_THRESHOLD_MS = 2000.0  # 2 seconds
    EFFICIENCY_BONUS = 0.1
    ATTEMPT_PENALTY_PER_STEP = 0.02
    TIME_PATIENCE_FACTOR = 0.05
    
    # Code quality thresholds
    CLEAN_CODE_THRESHOLD_LINES = 10
    CLEAN_CODE_BONUS = 0.05  # Small bonus for elegance
    
    # Complexity detection (empirical)
    QUADRATIC_TIME_THRESHOLD_MS = 3000.0  # Solutions >3s likely O(n²)
    COMPLEXITY_PENALTY = 0.15

    @staticmethod
    def detect_complexity_class(
        time_ms_total: float,
        code_lines: int,
        passed_cases: int,
        total_cases: int
    ) -> tuple[str, float]:
        """
        Detect algorithmic complexity class and return penalty.
        
        Args:
            time_ms_total: Total execution time in ms
            code_lines: Lines of code
            passed_cases: Tests passed
            total_cases: Total tests
            
        Returns:
            (complexity_class, penalty): e.g., ("O(n)", 0.0) or ("O(n²)", -0.15)
        """
        if passed_cases < total_cases:
            return ("unknown", 0.0)  # Can't detect if not all tests pass
        
        if time_ms_total > RewardCalculator.QUADRATIC_TIME_THRESHOLD_MS:
            return ("O(n²)", -RewardCalculator.COMPLEXITY_PENALTY)
        elif time_ms_total < 100.0 and code_lines < 20:
            return ("O(1) or O(log n)", 0.0)
        elif time_ms_total < 500.0:
            return ("O(n)", 0.0)
        else:
            return ("O(n log n)", 0.0)

    @staticmethod
    def calculate_code_quality_bonus(
        code_lines: int,
        passed_cases: int,
        total_cases: int
    ) -> tuple[float, str]:
        """
        Calculate bonus for clean, elegant code.
        
        Args:
            code_lines: Number of lines in solution
            passed_cases: Tests passed
            total_cases: Total tests
            
        Returns:
            (bonus, explanation): e.g., (0.05, "Clean, concise solution")
        """
        if passed_cases < total_cases:
            return (0.0, "Not all tests passed")
        
        if code_lines <= RewardCalculator.CLEAN_CODE_THRESHOLD_LINES:
            return (
                RewardCalculator.CLEAN_CODE_BONUS,
                f"Clean solution ({code_lines} lines) - very elegant"
            )
        elif code_lines <= 15:
            return (0.02, f"Concise solution ({code_lines} lines)")
        else:
            return (0.0, "Solution works but could be more concise")

    @staticmethod
    def calculate_improvement_bonus(
        current_passed: int,
        total_cases: int,
        previous_passed: Optional[int] = None,
        step_count: int = 1
    ) -> tuple[float, str]:
        """
        Reward agent for improving from previous attempt.
        
        Args:
            current_passed: Tests passed in current attempt
            total_cases: Total test cases
            previous_passed: Tests passed in previous attempt
            step_count: Current step number
            
        Returns:
            (bonus, explanation)
        """
        if previous_passed is None or step_count <= 1:
            return (0.0, "First attempt")
        
        improvement = current_passed - previous_passed
        if improvement > 0:
            bonus = 0.1 * min(improvement / total_cases, 0.1)  # Max 0.1 bonus
            return (
                bonus,
                f"Improvement: {previous_passed}→{current_passed} tests passed (+{improvement})"
            )
        else:
            return (0.0, "No improvement from previous attempt")

    @staticmethod
    def calculate(
        passed_cases: int,
        total_cases: int,
        time_ms_total: float,
        step_count: int,
        code_lines: int,
        error_type: str = None,
        error_message: str = None,
        test_results: List[Dict[str, Any]] = None,
        previous_passed: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Calculate rich reward breakdown for RL training.
        
        Components:
        1. Test pass rate (primary signal)
        2. Efficiency bonus (execution time < 2s)
        3. Complexity penalty (O(n²) detection)
        4. Code quality bonus (elegance, conciseness)
        5. Improvement bonus (learning from feedback)
        6. Attempt penalty (encourage solving quickly)
        
        Returns:
            {
                "reward": float,  # Final clipped [0, 1]
                "reward_breakdown": {
                    "test_pass_rate": float,
                    "efficiency_bonus": float,
                    "complexity_penalty": float,
                    "code_quality_bonus": float,
                    "improvement_bonus": float,
                    "attempt_penalty": float,
                    "explanation": str
                },
                ... (other fields)
            }
        """
        # Primary: test pass rate
        if total_cases == 0:
            primary_reward = 0.0
        else:
            primary_reward = passed_cases / total_cases

        # Efficiency bonus
        efficiency_bonus = 0.0
        if passed_cases == total_cases:
            if time_ms_total < RewardCalculator.EFFICIENCY_THRESHOLD_MS:
                efficiency_bonus = RewardCalculator.EFFICIENCY_BONUS
            else:
                excess_ms = time_ms_total - RewardCalculator.EFFICIENCY_THRESHOLD_MS
                efficiency_bonus = -min(0.05, excess_ms / 1000 * RewardCalculator.TIME_PATIENCE_FACTOR)

        # Complexity penalty (O(n²) detection)
        complexity_class, complexity_penalty = RewardCalculator.detect_complexity_class(
            time_ms_total, code_lines, passed_cases, total_cases
        )

        # Code quality bonus (elegance)
        code_quality_bonus, code_quality_explanation = RewardCalculator.calculate_code_quality_bonus(
            code_lines, passed_cases, total_cases
        )

        # Improvement bonus (learning signal)
        improvement_bonus, improvement_explanation = RewardCalculator.calculate_improvement_bonus(
            passed_cases, total_cases, previous_passed, step_count
        )

        # Attempt penalty (encourage solving in few steps)
        attempt_penalty = -(step_count - 1) * RewardCalculator.ATTEMPT_PENALTY_PER_STEP

        # Final reward
        final_reward = (
            primary_reward +
            efficiency_bonus +
            complexity_penalty +
            code_quality_bonus +
            improvement_bonus +
            attempt_penalty
        )
        final_reward = max(0.0, min(1.0, final_reward))

        # Build explanation
        explanations = []
        if passed_cases == total_cases:
            explanations.append(f"✓ All {total_cases} tests passed")
        else:
            explanations.append(f"✗ {passed_cases}/{total_cases} tests passed")
        
        if efficiency_bonus > 0:
            explanations.append(f"⚡ Fast execution ({time_ms_total:.0f}ms)")
        elif efficiency_bonus < 0:
            explanations.append(f"🐢 Slow execution ({time_ms_total:.0f}ms)")
        
        if complexity_penalty < 0:
            explanations.append(f"⚠️ Complexity: {complexity_class} - try using hashtable/set instead of nested loop")
        elif complexity_class in ("O(1) or O(log n)", "O(n)"):
            explanations.append(f"✅ {complexity_class} solution")
        
        if code_quality_bonus > 0:
            explanations.append(f"🎯 {code_quality_explanation}")
        
        if improvement_bonus > 0:
            explanations.append(f"📈 {improvement_explanation}")

        per_test_times = None
        if test_results:
            per_test_times = [r.get("time_ms", 0.0) for r in test_results]

        return {
            "reward": round(final_reward, 4),
            "reward_breakdown": {
                "test_pass_rate": round(primary_reward, 4),
                "efficiency_bonus": round(efficiency_bonus, 4),
                "complexity_penalty": round(complexity_penalty, 4),
                "code_quality_bonus": round(code_quality_bonus, 4),
                "improvement_bonus": round(improvement_bonus, 4),
                "attempt_penalty": round(attempt_penalty, 4),
                "complexity_class": complexity_class,
                "explanation": " | ".join(explanations)
            },
            # Legacy fields for compatibility
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
        """Classify error into a category."""
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
