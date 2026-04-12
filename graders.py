"""
APEX Engineering Benchmark - Graders
Scoring logic for each domain
"""

import re
import pandas as pd
from typing import Dict, List, Any, Optional
from models import RewardInfo, Observation


class DataPipelineGrader:
    """Grader for data_pipeline domain - test pandas code submissions"""
    
    PRODUCTION_KEYWORDS = [
        "scale", "performance", "large", "efficient", "optimize",
        "vectorize", "apply", "memory", "fast", "gpu"
    ]
    
    def grade(self, code: str, task: Dict[str, Any], step_num: int) -> RewardInfo:
        """
        Grade submitted pandas code.
        
        Returns reward based on:
        - Test cases passed (60%)
        - Code quality (40%)
        """
        if not code or len(code.strip()) < 5:
            return self._make_reward(
                reward=0.0,
                done=False,
                passed=0,
                total=len(task.get("test_cases", [])),
                feedback="Code submission too short",
                task=task
            )
        
        # Strip markdown code fences — LLMs always wrap code in ```python ... ```
        import re as _re
        code = _re.sub(r"^```(?:python)?\s*", "", code.strip())
        code = _re.sub(r"```\s*$", "", code.strip())
        code = code.strip()
        
        # Try to execute code and run test cases
        passed_cases = 0
        total_cases = len(task.get("test_cases", []))
        
        try:
            # Create execution environment with all required libraries
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
            
            # Execute code (short timeout)
            exec(code, global_vars, local_vars)
            
            # Get function from locals
            func_name = task.get("function_name", "solve")
            if func_name not in local_vars:
                return self._make_reward(
                    reward=0.15,
                    done=False,
                    passed=0,
                    total=total_cases,
                    feedback=f"Function '{func_name}' not defined in code",
                    task=task
                )
            
            func = local_vars[func_name]
            
            # Validate function is callable
            if not callable(func):
                return self._make_reward(
                    reward=0.15,
                    done=False,
                    passed=0,
                    total=total_cases,
                    feedback=f"'{func_name}' is not callable",
                    task=task
                )
            
            # Run test cases
            for test_case in task.get("test_cases", []):
                try:
                    # Create DataFrame from input
                    input_data = test_case.get("input", {})
                    if isinstance(input_data, dict):
                        df = pd.DataFrame(input_data)
                    else:
                        df = input_data
                    
                    # Execute function
                    result = func(df)
                    
                    # Check expected output
                    expected = test_case.get("expected")
                    if self._check_result(result, expected):
                        passed_cases += 1
                
                except Exception as test_err:
                    # Test case failed
                    pass
        
        except SyntaxError as e:
            return self._make_reward(
                reward=0.0,
                done=False,
                passed=0,
                total=total_cases,
                feedback=f"Syntax error: {str(e)[:50]}",
                task=task
            )
        except Exception as e:
            # Execution error
            return self._make_reward(
                reward=0.15,
                done=False,
                passed=0,
                total=total_cases,
                feedback=f"Runtime error: {type(e).__name__}",
                task=task
            )
        
        # Calculate reward with strict bounds
        if passed_cases == 0:
            # No test cases passed - low reward floor
            base_reward = 0.0
        elif passed_cases < total_cases:
            # Partial credit - between 0.3 and 0.8
            base_reward = 0.3 + (0.5 * (passed_cases / total_cases))
        else:
            # All test cases passed - can earn bonus
            base_reward = 0.85
        
        # Bonus for efficient code (only if passing most tests)
        efficiency_bonus = 0.0
        if passed_cases >= total_cases * 0.8:
            # Full points: check code quality
            if "groupby" in code and ("sum" in code or "agg" in code):
                efficiency_bonus = 0.10
            elif "apply" in code and "lambda" in code:
                efficiency_bonus = 0.05
        
        # Final reward with strict capping
        final_reward = base_reward + efficiency_bonus
        
        # Caps:
        # - Perfect code (all tests pass + bonus) = 1.0
        # - Very good code (all tests + small bonus) = 0.95
        # - Good code (all tests) = 0.85
        # - Partial = 0.3-0.8
        # - Bad/error = 0.1-0.15
        
        if passed_cases == total_cases and efficiency_bonus > 0.05:
            final_reward = 1.0  # Perfect!
        elif passed_cases == total_cases:
            final_reward = 0.95  # Very good
        else:
            final_reward = min(0.8, final_reward)  # Cap partial solutions at 0.8
        
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
        """Check if result matches expected output"""
        try:
            # Handle int expected = row count check (e.g. expected=2 means len(result)==2)
            if isinstance(expected, int) and isinstance(result, (pd.DataFrame, pd.Series)):
                return len(result) == expected
            elif isinstance(expected, int) and hasattr(result, '__len__'):
                return len(result) == expected
            elif isinstance(expected, dict) and isinstance(result, (dict, pd.Series)):
                if isinstance(result, pd.Series):
                    result = result.to_dict()
                # Allow approximate match for float values
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
        except:
            return False
    
    def _make_reward(self, reward: float, done: bool, passed: int,
                     total: int, feedback: str, task: Dict) -> RewardInfo:
        """Helper to create RewardInfo object"""
        return RewardInfo(
            session_id="session",
            task_id=task.get("task_id", "unknown"),
            reward=max(0.01, min(0.99, reward)),
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
        """
        Grade code review submission.
        
        Returns reward based on:
        - Production keywords mentioned (60%)
        - Technical quality (40%)
        """
        if not review_text or len(review_text.strip()) < 20:
            return self._make_reward(
                reward=0.0,
                done=True,
                feedback="Review too short - no credit awarded",
                task=task
            )
        
        review_lower = review_text.lower()
        
        # Check production keywords
        expected_prod_kw = task.get("expected_production_keywords", self.PRODUCTION_KEYWORDS[:5])
        prod_keywords_found = [
            kw for kw in expected_prod_kw
            if kw.lower() in review_lower
        ]
        prod_score = len(prod_keywords_found) / max(len(expected_prod_kw), 1)
        
        # Check technical keywords
        expected_tech_kw = task.get("expected_fix_keywords", self.TECHNICAL_KEYWORDS[:5])
        tech_keywords_found = [
            kw for kw in expected_tech_kw
            if kw.lower() in review_lower
        ]
        tech_score = len(tech_keywords_found) / max(len(expected_tech_kw), 1)
        
        # Weighted combination with floor
        base_reward = (prod_score * 0.6) + (tech_score * 0.4)
        base_reward = max(0.0, min(1.0, base_reward))  # Clip to valid range [0.0, 1.0]
        
        # Boost if comprehensive
        final_reward = base_reward
        if len(review_text) > 200 and prod_keywords_found and tech_keywords_found:
            final_reward = min(1.0, final_reward + 0.15)
        
        # Cap at 0.95 unless perfect
        if final_reward < 1.0:
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
        """Helper to create RewardInfo object"""
        return RewardInfo(
            session_id="session",
            task_id=task.get("task_id", "unknown"),
            reward=max(0.01, min(0.99, reward)),
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
        """
        Grade incident diagnosis for current step.
        
        Each step has expected_keywords to identify.
        Score = keywords_matched / total_keywords
        """
        if previous_scores is None:
            previous_scores = []
        
        if not diagnosis_text or len(diagnosis_text.strip()) < 5:
            return self._make_reward(
                reward=0.0,
                done=False,
                step_num=step_num,
                feedback="Diagnosis too short",
                task=task,
                step_scores=[0.0]
            )
        
        diagnosis_lower = diagnosis_text.lower()
        
        # Get expected keywords for this step
        steps = task.get("steps", [])
        if step_num <= len(steps):
            step_info = steps[step_num - 1]
            expected_kw = step_info.get("expected_keywords", [])
        else:
            expected_kw = []
        
        # Find keywords in response using word-level matching (more flexible)
        keywords_found = []
        for kw in expected_kw:
            kw_lower = kw.lower()
            # Substring match catches stemmed forms (cascade->cascading, hammer->hammering)
            if kw_lower in diagnosis_lower:
                keywords_found.append(kw)
            # Fallback: word-set match for multi-word phrases in different order
            elif set(kw_lower.split()).issubset(set(diagnosis_lower.split())):
                keywords_found.append(kw)
        
        if expected_kw:
            step_reward = len(keywords_found) / len(expected_kw)
        else:
            step_reward = 0.3
        
        # Ensure valid reward bounds
        step_reward = max(0.0, min(1.0, step_reward))
        
        # Boost if comprehensive
        if len(diagnosis_text) > 100 and len(keywords_found) > len(expected_kw) / 2:
            step_reward = min(1.0, step_reward + 0.1)
        
        # Check if episode is done
        is_last_step = step_num >= len(steps)
        done = is_last_step
        
        # Calculate cumulative reward
        all_scores = previous_scores + [step_reward]
        cumulative_reward = max(all_scores) if all_scores else step_reward
        
        # Ensure reward bounds
        cumulative_reward = max(0.0, min(1.0, cumulative_reward))
        
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
        """Helper to create RewardInfo object"""
        return RewardInfo(
            session_id="session",
            task_id=task.get("task_id", "unknown"),
            reward=max(0.01, min(0.99, reward)),
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
            step_scores=step_scores or [],
            feedback=feedback,
            info={}
        )
