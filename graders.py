"""
APEX Engineering Benchmark - Graders
Scoring logic for each domain
"""

import re
import pandas as pd
from typing import Dict, List, Any, Optional
from models import RewardInfo, Observation

# Phase 2 compliance: all rewards must be strictly in (0, 1)
def safe_score(x: float) -> float:
    return max(0.01, min(0.99, float(x)))


class DataPipelineGrader:
    """Grader for data_pipeline domain - test pandas code submissions"""

    def grade(self, code: str, task: Dict[str, Any], step_num: int) -> RewardInfo:
        if not code or len(code.strip()) < 5:
            return self._make_reward(
                reward=0.05,
                done=False,
                passed=0,
                total=len(task.get("test_cases", [])),
                feedback="Code submission too short",
                task=task
            )

        # Strip markdown code fences
        import re as _re
        code = _re.sub(r"^```(?:python)?\s*", "", code.strip())
        code = _re.sub(r"```\s*$", "", code.strip())
        code = code.strip()

        passed_cases = 0
        total_cases = len(task.get("test_cases", []))

        try:
            import datetime, re as _re_module, json, math, collections
            local_vars = {}
            global_vars = {
                "pd": pd,
                "__import__": __import__,
                "datetime": datetime,
                "re": _re_module,
                "json": json,
                "math": math,
                "collections": collections,
            }

            exec(code, global_vars, local_vars)

            func_name = task.get("function_name", "solve")
            if func_name not in local_vars:
                return self._make_reward(
                    reward=0.10,
                    done=False,
                    passed=0,
                    total=total_cases,
                    feedback=f"Function ''{func_name}'' not defined in code",
                    task=task
                )

            func = local_vars[func_name]

            if not callable(func):
                return self._make_reward(
                    reward=0.10,
                    done=False,
                    passed=0,
                    total=total_cases,
                    feedback=f"''{func_name}'' is not callable",
                    task=task
                )

            for test_case in task.get("test_cases", []):
                try:
                    input_data = test_case.get("input", {})
                    df = pd.DataFrame(input_data) if isinstance(input_data, dict) else input_data
                    result = func(df)
                    expected = test_case.get("expected")
                    if self._check_result(result, expected):
                        passed_cases += 1
                except Exception:
                    pass

        except SyntaxError as e:
            return self._make_reward(
                reward=0.02,
                done=False,
                passed=0,
                total=total_cases,
                feedback=f"Syntax error: {str(e)[:50]}",
                task=task
            )
        except Exception as e:
            return self._make_reward(
                reward=0.10,
                done=False,
                passed=0,
                total=total_cases,
                feedback=f"Runtime error: {type(e).__name__}",
                task=task
            )

        if passed_cases == 0:
            base_reward = 0.05
        elif passed_cases < total_cases:
            base_reward = 0.30 + (0.50 * (passed_cases / total_cases))
        else:
            base_reward = 0.85

        efficiency_bonus = 0.0
        if passed_cases >= total_cases * 0.8:
            if "groupby" in code and ("sum" in code or "agg" in code):
                efficiency_bonus = 0.10
            elif "apply" in code and "lambda" in code:
                efficiency_bonus = 0.05

        if passed_cases == total_cases and efficiency_bonus > 0.05:
            final_reward = 0.98
        elif passed_cases == total_cases:
            final_reward = 0.94
        else:
            final_reward = min(0.79, base_reward + efficiency_bonus)

        done = passed_cases == total_cases
        feedback = f"Passed {passed_cases}/{total_cases} test cases"
        if efficiency_bonus > 0:
            feedback += " + efficiency bonus"

        return self._make_reward(
            reward=final_reward,
            done=done,
            passed=passed_cases,
            total=total_cases,
            feedback=feedback,
            task=task
        )

    def _check_result(self, result: Any, expected: Any) -> bool:
        try:
            if isinstance(expected, int) and isinstance(result, (pd.DataFrame, pd.Series)):
                return len(result) == expected
            elif isinstance(expected, int) and hasattr(result, '__len__'):
                return len(result) == expected
            elif isinstance(expected, dict) and isinstance(result, (dict, pd.Series)):
                if isinstance(result, pd.Series):
                    result = result.to_dict()
                if all(isinstance(v, (int, float)) for v in expected.values()):
                    return all(
                        abs(float(result.get(k, 0)) - float(v)) < 0.01
                        for k, v in expected.items()
                    )
                return result == expected
            elif isinstance(expected, pd.DataFrame) and isinstance(result, pd.DataFrame):
                return result.equals(expected)
            elif isinstance(expected, list) and isinstance(result, list):
                return result == expected
            else:
                return str(result) == str(expected)
        except Exception:
            return False

    def _make_reward(self, reward: float, done: bool, passed: int,
                     total: int, feedback: str, task: Dict) -> RewardInfo:
        return RewardInfo(
            session_id="session",
            task_id=task.get("task_id", "unknown"),
            reward=safe_score(reward),
            done=done,
            observation=Observation(
                session_id="session",
                task_id=task.get("task_id", "unknown"),
                domain="data_pipeline",
                difficulty=task.get("difficulty", "easy"),
                title=task.get("title", ""),
                description=task.get("description", ""),
                passed_cases=passed,
                total_cases=total,
                feedback=feedback
            ),
            passed_cases=passed,
            total_cases=total,
            feedback=feedback,
            info={}
        )


class CodeReviewGrader:
    """Grader for code_review domain - evaluate code reviews"""

    PRODUCTION_KEYWORDS = [
        "scale", "timeout", "users", "crash", "data loss",
        "memory", "latency", "n+1", "race condition", "deadlock",
        "overflow", "injection", "concurrent", "thread"
    ]

    TECHNICAL_KEYWORDS = [
        "fix", "refactor", "optimize", "replace", "remove",
        "add", "check", "validate", "cache", "index",
        "lock", "atomic", "batch", "aggregate", "select_related"
    ]

    def grade(self, review_text: str, task: Dict[str, Any], step_num: int) -> RewardInfo:
        if not review_text or len(review_text.strip()) < 20:
            return self._make_reward(
                reward=0.05,
                done=True,
                feedback="Review too short - minimal credit awarded",
                task=task
            )

        review_lower = review_text.lower()

        expected_prod_kw = task.get("expected_production_keywords", self.PRODUCTION_KEYWORDS[:5])
        prod_keywords_found = [kw for kw in expected_prod_kw if kw.lower() in review_lower]
        prod_score = len(prod_keywords_found) / max(len(expected_prod_kw), 1)

        expected_tech_kw = task.get("expected_fix_keywords", self.TECHNICAL_KEYWORDS[:5])
        tech_keywords_found = [kw for kw in expected_tech_kw if kw.lower() in review_lower]
        tech_score = len(tech_keywords_found) / max(len(expected_tech_kw), 1)

        base_reward = (prod_score * 0.6) + (tech_score * 0.4)

        final_reward = base_reward
        if len(review_text) > 200 and prod_keywords_found and tech_keywords_found:
            final_reward = min(0.95, final_reward + 0.15)

        final_reward = min(0.95, final_reward)

        feedback = f"Production impact: {len(prod_keywords_found)}/{len(expected_prod_kw)} | "
        feedback += f"Technical: {len(tech_keywords_found)}/{len(expected_tech_kw)}"

        return self._make_reward(
            reward=final_reward,
            done=True,
            feedback=feedback,
            task=task,
            keywords_found=prod_keywords_found + tech_keywords_found
        )

    def _make_reward(self, reward: float, done: bool, feedback: str,
                     task: Dict, keywords_found: List[str] = None) -> RewardInfo:
        return RewardInfo(
            session_id="session",
            task_id=task.get("task_id", "unknown"),
            reward=safe_score(reward),
            done=done,
            observation=Observation(
                session_id="session",
                task_id=task.get("task_id", "unknown"),
                domain="code_review",
                difficulty=task.get("difficulty", "easy"),
                title=task.get("title", ""),
                description=task.get("description", ""),
                feedback=feedback
            ),
            production_keywords_found=keywords_found or [],
            feedback=feedback,
            info={}
        )


class IncidentDebugGrader:
    """Grader for incident_debug domain - multi-step diagnostics"""

    def grade(self, diagnosis_text: str, task: Dict[str, Any],
              step_num: int, previous_scores: List[float] = None) -> RewardInfo:
        if previous_scores is None:
            previous_scores = []

        if not diagnosis_text or len(diagnosis_text.strip()) < 5:
            return self._make_reward(
                reward=0.05,
                done=False,
                step_num=step_num,
                feedback="Diagnosis too short",
                task=task,
                step_scores=[0.05]
            )

        diagnosis_lower = diagnosis_text.lower()

        steps = task.get("steps", [])
        if step_num <= len(steps):
            step_info = steps[step_num - 1]
            expected_kw = step_info.get("expected_keywords", [])
        else:
            expected_kw = []

        keywords_found = []
        for kw in expected_kw:
            kw_lower = kw.lower()
            if kw_lower in diagnosis_lower:
                keywords_found.append(kw)
            elif set(kw_lower.split()).issubset(set(diagnosis_lower.split())):
                keywords_found.append(kw)

        if expected_kw:
            step_reward = len(keywords_found) / len(expected_kw)
        else:
            step_reward = 0.30

        step_reward = safe_score(step_reward)

        if len(diagnosis_text) > 100 and len(keywords_found) > len(expected_kw) / 2:
            step_reward = min(0.99, step_reward + 0.10)

        is_last_step = step_num >= len(steps)
        done = is_last_step

        all_scores = previous_scores + [step_reward]
        cumulative_reward = safe_score(max(all_scores))

        feedback = f"Step {step_num}/{len(steps)}: {len(keywords_found)}/{len(expected_kw)} keywords matched"

        return self._make_reward(
            reward=cumulative_reward,
            done=done,
            step_num=step_num,
            feedback=feedback,
            task=task,
            step_scores=all_scores
        )

    def _make_reward(self, reward: float, done: bool, step_num: int,
                     feedback: str, task: Dict, step_scores: List[float] = None) -> RewardInfo:
        return RewardInfo(
            session_id="session",
            task_id=task.get("task_id", "unknown"),
            reward=safe_score(reward),
            done=done,
            observation=Observation(
                session_id="session",
                task_id=task.get("task_id", "unknown"),
                domain="incident_debug",
                difficulty=task.get("difficulty", "easy"),
                title=task.get("title", ""),
                description=task.get("description", ""),
                step_number=step_num,
                feedback=feedback
            ),
            step_scores=[safe_score(s) for s in (step_scores or [])],
            feedback=feedback,
            info={}
        )