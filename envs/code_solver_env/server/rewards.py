"""Reward calculation for data pipeline RL environment - SOLVE/REVIEW/DEBUG modes"""

from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


class PipelineRewardCalculator:
    """
    Calculate rewards for data pipeline RL environment with 3 task modes:
    
    1. SOLVE mode: Write code from scratch
       - base_reward = 0.4 * visible_score + 0.6 * hidden_score
       - attempt_penalty = -0.02 * (step - 1)
       - efficiency_bonus = +0.05 if solved in <= 2 steps
    
    2. REVIEW mode: Identify and fix bugs (max 3 steps)
       - bug_location: +0.25 if within 3 lines
       - bug_type: +0.20 if correct categorization
       - explanation: +0.20 if mentions root cause
       - fixed_code: +0.35 if passes all tests
    
    3. DEBUG mode: Fix crashing code (multi-step)
       - reward = tests_passing / total_tests
       - regression_penalty = -0.15 if worse than previous step
       - cascading_bonus = +0.1 if all cascading errors fixed (hard only)
    """

    # SOLVE mode constants
    SOLVE_VISIBLE_WEIGHT = 0.4
    SOLVE_HIDDEN_WEIGHT = 0.6
    SOLVE_ATTEMPT_PENALTY = 0.02
    SOLVE_EFFICIENCY_BONUS = 0.05
    SOLVE_EFFICIENCY_STEPS = 2

    # REVIEW mode constants
    REVIEW_BUG_LOCATION_BONUS = 0.25
    REVIEW_BUG_TYPE_BONUS = 0.20
    REVIEW_EXPLANATION_BONUS = 0.20
    REVIEW_FIXED_CODE_BONUS = 0.35
    REVIEW_LOCATION_TOLERANCE = 3  # Lines tolerance

    # DEBUG mode constants
    DEBUG_REGRESSION_PENALTY = 0.15
    DEBUG_CASCADING_BONUS = 0.10

    @staticmethod
    def calculate_solve_reward(
        visible_passed: int,
        visible_total: int,
        hidden_passed: int,
        hidden_total: int,
        step_count: int,
        task_difficulty: str = "easy"
    ) -> Dict[str, Any]:
        """
        Calculate reward for SOLVE mode (agent writes code from scratch).
        
        Args:
            visible_passed: Number of visible test cases passed
            visible_total: Total visible test cases
            hidden_passed: Number of hidden test cases passed
            hidden_total: Total hidden test cases
            step_count: Step number (1-indexed)
            task_difficulty: Task difficulty (easy, medium, hard)
            
        Returns:
            {
                "reward": float,  # Final reward [0.0, 1.0]
                "breakdown": { ... },
                "done": bool  # Episode complete (all tests passed or max steps)
            }
        """
        # Visible and hidden test scores
        visible_score = visible_passed / visible_total if visible_total > 0 else 0.0
        hidden_score = hidden_passed / hidden_total if hidden_total > 0 else 0.0
        
        # Base reward = weighted average
        base_reward = (
            PipelineRewardCalculator.SOLVE_VISIBLE_WEIGHT * visible_score +
            PipelineRewardCalculator.SOLVE_HIDDEN_WEIGHT * hidden_score
        )
        
        # Attempt penalty (encourage solving in few steps)
        attempt_penalty = -(step_count - 1) * PipelineRewardCalculator.SOLVE_ATTEMPT_PENALTY
        
        # Efficiency bonus (solved in <= 2 steps)
        efficiency_bonus = 0.0
        if step_count <= PipelineRewardCalculator.SOLVE_EFFICIENCY_STEPS and \
           hidden_passed == hidden_total and visible_passed == visible_total:
            efficiency_bonus = PipelineRewardCalculator.SOLVE_EFFICIENCY_BONUS
        
        # Final reward (clipped to [0, 1])
        final_reward = base_reward + attempt_penalty + efficiency_bonus
        final_reward = max(0.0, min(1.0, final_reward))
        
        # Episode complete if all tests pass
        done = (hidden_passed == hidden_total and visible_passed == visible_total)
        
        return {
            "reward": round(final_reward, 4),
            "done": done,
            "breakdown": {
                "visible_score": round(visible_score, 4),
                "hidden_score": round(hidden_score, 4),
                "base_reward": round(base_reward, 4),
                "attempt_penalty": round(attempt_penalty, 4),
                "efficiency_bonus": round(efficiency_bonus, 4),
                "visible_passed": visible_passed,
                "visible_total": visible_total,
                "hidden_passed": hidden_passed,
                "hidden_total": hidden_total,
                "step": step_count,
                "explanation": f"Step {step_count}: {hidden_passed}/{hidden_total} hidden, {visible_passed}/{visible_total} visible"
            }
        }

    @staticmethod
    def calculate_review_reward(
        bug_location_correct: bool,
        bug_location_agent: str,
        bug_location_true: str,
        bug_type_correct: bool,
        explanation_has_keywords: bool,
        fixed_code_all_passing: bool,
        fixed_code_tests_passed: int,
        fixed_code_tests_total: int,
        step_count: int
    ) -> Dict[str, Any]:
        """
        Calculate reward for REVIEW mode (agent identifies and fixes bugs).
        
        Scoring:
            - Bug location: +0.25 if within 3 lines of true location
            - Bug type: +0.20 if exact match
            - Explanation: +0.20 if mentions root cause keywords
            - Fixed code: +0.35 if passes all test cases
        
        Args:
            bug_location_correct: Is bug location within 3 lines?
            bug_location_agent: Agent's identified location
            bug_location_true: True bug location
            bug_type_correct: Does agent's bug_type match true type?
            explanation_has_keywords: Does explanation contain keywords?
            fixed_code_all_passing: Do all tests pass for fixed code?
            fixed_code_tests_passed: Number of tests passed
            fixed_code_tests_total: Total tests
            step_count: Step number (1-indexed, max 3)
            
        Returns:
            {
                "reward": float,
                "breakdown": { ... },
                "done": bool
            }
        """
        location_bonus = PipelineRewardCalculator.REVIEW_BUG_LOCATION_BONUS if bug_location_correct else 0.0
        type_bonus = PipelineRewardCalculator.REVIEW_BUG_TYPE_BONUS if bug_type_correct else 0.0
        explanation_bonus = PipelineRewardCalculator.REVIEW_EXPLANATION_BONUS if explanation_has_keywords else 0.0
        
        # Fixed code bonus: 0.35 if all pass, scaled if partial
        if fixed_code_all_passing:
            fixed_code_bonus = PipelineRewardCalculator.REVIEW_FIXED_CODE_BONUS
        else:
            fixed_code_bonus = (fixed_code_tests_passed / max(1, fixed_code_tests_total)) * \
                              PipelineRewardCalculator.REVIEW_FIXED_CODE_BONUS
        
        # Total reward
        final_reward = location_bonus + type_bonus + explanation_bonus + fixed_code_bonus
        final_reward = max(0.0, min(1.0, final_reward))
        
        # Episode complete if all passing or max steps
        done = fixed_code_all_passing or step_count >= 3
        
        return {
            "reward": round(final_reward, 4),
            "done": done,
            "breakdown": {
                "bug_location_bonus": round(location_bonus, 4),
                "bug_type_bonus": round(type_bonus, 4),
                "explanation_bonus": round(explanation_bonus, 4),
                "fixed_code_bonus": round(fixed_code_bonus, 4),
                "bug_location_correct": bug_location_correct,
                "bug_type_correct": bug_type_correct,
                "explanation_has_keywords": explanation_has_keywords,
                "fixed_code_tests": f"{fixed_code_tests_passed}/{fixed_code_tests_total}",
                "step": step_count
            }
        }

    @staticmethod
    def calculate_debug_reward(
        tests_passed: int,
        tests_total: int,
        step_count: int,
        previous_tests_passed: Optional[int] = None,
        is_cascading_hard: bool = False,
        all_cascading_fixed: bool = False
    ) -> Dict[str, Any]:
        """
        Calculate reward for DEBUG mode (agent fixes crashing/wrong code).
        
        Scoring:
            - Base: tests_passed / tests_total
            - Regression penalty: -0.15 if fewer tests than previous step
            - Cascading bonus: +0.10 if all errors fixed (hard only)
        
        Args:
            tests_passed: Tests passing after fix
            tests_total: Total tests
            step_count: Step number (1-indexed, max 5)
            previous_tests_passed: Tests in previous step
            is_cascading_hard: Is this a cascading error task?
            all_cascading_fixed: Are all errors fixed?
            
        Returns:
            {
                "reward": float,
                "breakdown": { ... },
                "done": bool
            }
        """
        # Base reward
        base_reward = tests_passed / max(1, tests_total)
        
        # Regression penalty
        regression_penalty = 0.0
        if previous_tests_passed is not None and tests_passed < previous_tests_passed:
            regression_penalty = -PipelineRewardCalculator.DEBUG_REGRESSION_PENALTY
        
        # Cascading bonus
        cascading_bonus = 0.0
        if is_cascading_hard and all_cascading_fixed:
            cascading_bonus = PipelineRewardCalculator.DEBUG_CASCADING_BONUS
        
    @staticmethod
    def calculate_debug_reward(
        tests_passed: int,
        tests_total: int,
        step_count: int,
        previous_tests_passed: Optional[int] = None,
        is_cascading_hard: bool = False,
        all_cascading_fixed: bool = False
    ) -> Dict[str, Any]:
        """
        Calculate reward for DEBUG mode (agent fixes crashing/wrong code).
        
        Scoring:
            - Base: tests_passed / tests_total
            - Regression penalty: -0.15 if fewer tests than previous step
            - Cascading bonus: +0.10 if all errors fixed (hard only)
        
        Args:
            tests_passed: Tests passing after fix
            tests_total: Total tests
            step_count: Step number (1-indexed, max 5)
            previous_tests_passed: Tests in previous step
            is_cascading_hard: Is this a cascading error task?
            all_cascading_fixed: Are all errors fixed?
            
        Returns:
            {
                "reward": float,
                "breakdown": { ... },
                "done": bool
            }
        """
        # Base reward
        base_reward = tests_passed / max(1, tests_total)
        
        # Regression penalty
        regression_penalty = 0.0
        if previous_tests_passed is not None and tests_passed < previous_tests_passed:
            regression_penalty = -PipelineRewardCalculator.DEBUG_REGRESSION_PENALTY
        
        # Cascading bonus
        cascading_bonus = 0.0
        if is_cascading_hard and all_cascading_fixed:
            cascading_bonus = PipelineRewardCalculator.DEBUG_CASCADING_BONUS
        
        # Final reward
        final_reward = base_reward + regression_penalty + cascading_bonus
        final_reward = max(0.0, min(1.0, final_reward))
        
        # Episode complete if all pass or max steps
        done = (tests_passed == tests_total) or step_count >= 5
        
        return {
            "reward": round(final_reward, 4),
            "done": done,
            "breakdown": {
                "base_reward": round(base_reward, 4),
                "regression_penalty": round(regression_penalty, 4),
                "cascading_bonus": round(cascading_bonus, 4),
                "tests_passed": tests_passed,
                "tests_total": tests_total,
                "step": step_count
            }
        }

    # CODE REVIEW DOMAIN CONSTANTS
    CODE_REVIEW_PROBLEM_IDENTIFIED_BONUS = 0.20
    CODE_REVIEW_PRODUCTION_IMPACT_BONUS = 0.25
    CODE_REVIEW_FIX_APPROACH_BONUS = 0.20
    CODE_REVIEW_FIXED_CODE_BONUS = 0.35
    
    # Keywords for production impact evaluation
    PRODUCTION_IMPACT_KEYWORDS = [
        "scale", "production", "users", "timeout",
        "memory", "concurrent", "latency", "crash", "data loss",
        "oom", "oomed", "exhausted", "stampede", "cascade",
        "overflow", "overflow", "distributed", "transaction"
    ]

    @staticmethod
    def calculate_code_review_reward(
        problem_identified: bool,
        production_impact_text: str,
        production_impact_correct: bool,
        fix_approach_correct: bool,
        fixed_code_tests_passed: int,
        fixed_code_tests_total: int,
        step_count: int
    ) -> Dict[str, Any]:
        """
        Calculate reward for CODE_REVIEW domain task.
        
        Scoring (Production Code Review):
            - 0.20: Problem identified correctly
            - 0.25: Production impact mentioned (scale, users, performance, crashes)
            - 0.20: Fix approach is correct
            - 0.35: Fixed code passes all test cases
        
        Args:
            problem_identified: Agent correctly identified the problem
            production_impact_text: Agent's explanation of production impact
            production_impact_correct: Explanation mentions scale/performance/data loss
            fix_approach_correct: Fix approach is architecturally sound
            fixed_code_tests_passed: Tests passing in fixed code
            fixed_code_tests_total: Total tests for fixed code
            step_count: Step number (1-indexed, max 3)
            
        Returns:
            {
                "reward": float,
                "breakdown": { ... },
                "done": bool
            }
        """
        # Check for production impact keywords
        impact_text_lower = (production_impact_text or "").lower()
        has_impact_keyword = any(
            keyword in impact_text_lower 
            for keyword in PipelineRewardCalculator.PRODUCTION_IMPACT_KEYWORDS
        )
        production_impact_bonus = (
            PipelineRewardCalculator.CODE_REVIEW_PRODUCTION_IMPACT_BONUS 
            if (production_impact_correct or has_impact_keyword) else 0.0
        )
        
        # Problem identification bonus
        problem_bonus = (
            PipelineRewardCalculator.CODE_REVIEW_PROBLEM_IDENTIFIED_BONUS 
            if problem_identified else 0.0
        )
        
        # Fix approach bonus
        fix_approach_bonus = (
            PipelineRewardCalculator.CODE_REVIEW_FIX_APPROACH_BONUS 
            if fix_approach_correct else 0.0
        )
        
        # Fixed code bonus: 0.35 if all pass, scaled if partial
        if fixed_code_tests_passed == fixed_code_tests_total:
            fixed_code_bonus = PipelineRewardCalculator.CODE_REVIEW_FIXED_CODE_BONUS
        else:
            fixed_code_bonus = (fixed_code_tests_passed / max(1, fixed_code_tests_total)) * \
                              PipelineRewardCalculator.CODE_REVIEW_FIXED_CODE_BONUS
        
        # Total reward
        final_reward = problem_bonus + production_impact_bonus + fix_approach_bonus + fixed_code_bonus
        final_reward = max(0.0, min(1.0, final_reward))
        
        # Episode complete if all passing or max steps
        done = (fixed_code_tests_passed == fixed_code_tests_total) or step_count >= 3
        
        return {
            "reward": round(final_reward, 4),
            "done": done,
            "breakdown": {
                "problem_identified_bonus": round(problem_bonus, 4),
                "production_impact_bonus": round(production_impact_bonus, 4),
                "fix_approach_bonus": round(fix_approach_bonus, 4),
                "fixed_code_bonus": round(fixed_code_bonus, 4),
                "problem_identified": problem_identified,
                "production_impact_mentioned": production_impact_correct or has_impact_keyword,
                "fix_approach_correct": fix_approach_correct,
                "fixed_code_tests": f"{fixed_code_tests_passed}/{fixed_code_tests_total}",
                "step": step_count
            }
        }

    # INCIDENT DEBUG DOMAIN CONSTANTS
    INCIDENT_REGRESSION_PENALTY = 0.15
    INCIDENT_CASCADE_BONUS = 0.15
    INCIDENT_MAX_STEPS = 3

    @staticmethod
    def calculate_incident_debug_reward(
        steps_resolved: int,
        total_steps: int,
        current_step_correct: bool,
        previous_step_passing: Optional[bool] = None,
        is_hard_cascading: bool = False,
        all_cascading_fixed: bool = False
    ) -> Dict[str, Any]:
        """
        Calculate reward for INCIDENT_DEBUG domain (multi-step SRE scenarios).
        
        Scoring (Progressive Revelation):
            - Base: steps_resolved / total_steps
            - Regression penalty: -0.15 if current step breaks previous step
            - Cascade bonus: +0.15 if all steps in hard task fixed correctly
        
        Each step reveals next symptom only if current fix is correct.
        
        Args:
            steps_resolved: Number of steps correctly fixed
            total_steps: Total steps in incident (1, 2, or 3)
            current_step_correct: Is current step's fix correct?
            previous_step_passing: Was previous step's solution still working?
            is_hard_cascading: Is this a hard cascading incident?
            all_cascading_fixed: Are all steps in cascading incident fixed?
            
        Returns:
            {
                "reward": float,
                "breakdown": { ... },
                "done": bool
            }
        """
        # Base reward: proportion of steps resolved
        base_reward = steps_resolved / max(1, total_steps)
        
        # Regression penalty: -0.15 if fix breaks previous step
        regression_penalty = 0.0
        if previous_step_passing is False:
            regression_penalty = -PipelineRewardCalculator.INCIDENT_REGRESSION_PENALTY
        
        # Cascade bonus: +0.15 if all steps fixed (hard cascading only)
        cascade_bonus = 0.0
        if is_hard_cascading and all_cascading_fixed:
            cascade_bonus = PipelineRewardCalculator.INCIDENT_CASCADE_BONUS
        
        # Final reward
        final_reward = base_reward + regression_penalty + cascade_bonus
        final_reward = max(0.0, min(1.0, final_reward))
        
        # Episode complete if all steps resolved or max steps reached
        done = (steps_resolved == total_steps) or (steps_resolved >= PipelineRewardCalculator.INCIDENT_MAX_STEPS)
        
        return {
            "reward": round(final_reward, 4),
            "done": done,
            "breakdown": {
                "base_reward": round(base_reward, 4),
                "regression_penalty": round(regression_penalty, 4),
                "cascade_bonus": round(cascade_bonus, 4),
                "steps_resolved": steps_resolved,
                "total_steps": total_steps,
                "current_step_correct": current_step_correct,
                "previous_step_passing": previous_step_passing if previous_step_passing is not None else "N/A",
                "is_hard_cascading": is_hard_cascading,
                "explanation": f"Step {steps_resolved}/{total_steps} resolved; {final_reward:.2f} reward"
            }
        }


# Legacy compatibility
class RewardCalculator:
    """Backward compatibility wrapper - use PipelineRewardCalculator instead"""
    
    @staticmethod
    def calculate(**kwargs) -> Dict[str, Any]:
        """Deprecated - use PipelineRewardCalculator instead"""
        logger.warning("RewardCalculator deprecated. Use PipelineRewardCalculator.")
        return {
            "reward": 0.0,
            "passed_cases": 0,
            "total_cases": 0
        }
