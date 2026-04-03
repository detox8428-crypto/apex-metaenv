"""Code Solver Environment Implementation"""

import random
import subprocess
import tempfile
import json
import sys
from typing import Tuple, Dict, Any
from ..models import CodeSolverAction, CodeSolverObservation, CodeSolverState
from .problems import PROBLEMS, get_problem_by_id, get_problems_by_difficulty


class CodeSolverEnvironment:
    """RL Environment for code solving task"""

    def __init__(self):
        """Initialize the environment"""
        self._current_problem = None
        self._state = CodeSolverState()
        self._max_attempts = 3

    def reset(self, difficulty: str = None) -> CodeSolverObservation:
        """
        Reset environment: pick random problem (optionally filtered by difficulty)
        
        Args:
            difficulty: Optional filter for problem difficulty (easy/medium/hard)
            
        Returns:
            Initial observation with problem statement
        """
        # Pick a random problem
        if difficulty and difficulty in ["easy", "medium", "hard"]:
            available = get_problems_by_difficulty(difficulty)
            if not available:
                available = PROBLEMS
        else:
            available = PROBLEMS
        
        self._current_problem = random.choice(available)
        self._state.problem_id = self._current_problem["problem_id"]
        self._state.difficulty = self._current_problem["difficulty"]
        self._state.attempts = 0

        observation = CodeSolverObservation(
            problem_id=self._current_problem["problem_id"],
            title=self._current_problem["title"],
            description=self._current_problem["description"],
            function_signature=self._current_problem["function_signature"],
            examples=self._current_problem["examples"],
            constraints=self._current_problem["constraints"],
            difficulty=self._current_problem["difficulty"],
            test_results="",
            passed_cases=0,
            total_cases=len(self._current_problem["test_cases"]),
            error_message=""
        )

        return observation

    def step(self, action: CodeSolverAction) -> Tuple[CodeSolverObservation, float, bool]:
        """
        Execute agent's code against test cases
        
        Args:
            action: CodeSolverAction containing the agent's solution code
            
        Returns:
            (observation, reward, done): observation with results, reward (0.0-1.0), done flag
        """
        if not self._current_problem:
            return self._create_error_observation("Error: Environment not reset"), 0.0, True

        self._state.attempts += 1

        # Run test cases
        test_results = self._run_test_cases(action.code, self._current_problem)

        passed = test_results["passed"]
        total = test_results["total"]
        reward = passed / total if total > 0 else 0.0
        done = (reward == 1.0) or (self._state.attempts >= self._max_attempts)

        # Format test results feedback
        feedback_lines = []
        if test_results["error"]:
            feedback_lines.append(f"Error: {test_results['error']}")
        else:
            feedback_lines.append(f"Test Results: {passed}/{total} passed")
            for i, result in enumerate(test_results["results"], 1):
                status = "PASS" if result["passed"] else "FAIL"
                feedback_lines.append(f"  Test {i}: {status}")
                if not result["passed"]:
                    feedback_lines.append(f"    Input: {result['input']}")
                    feedback_lines.append(f"    Expected: {result['expected']}, Got: {result['actual']}")

        test_results_str = "\n".join(feedback_lines)

        observation = CodeSolverObservation(
            problem_id=self._current_problem["problem_id"],
            title=self._current_problem["title"],
            description=self._current_problem["description"],
            function_signature=self._current_problem["function_signature"],
            examples=self._current_problem["examples"],
            constraints=self._current_problem["constraints"],
            difficulty=self._current_problem["difficulty"],
            test_results=test_results_str,
            passed_cases=passed,
            total_cases=total,
            error_message=test_results["error"]
        )

        return observation, reward, done

    def _run_test_cases(self, code: str, problem: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run code against all test cases safely in subprocess
        
        Args:
            code: Agent's solution code
            problem: Problem definition with test cases
            
        Returns:
            Dict with: passed (int), total (int), results (list), error (str)
        """
        test_cases = problem["test_cases"]
        results = []
        passed = 0
        error = ""

        for i, test_case in enumerate(test_cases):
            test_input = test_case["input"]
            expected = test_case["expected"]

            try:
                # Create test script
                test_script = self._create_test_script(code, problem["function_signature"], test_input, expected)

                # Run in subprocess with timeout
                result = subprocess.run(
                    [sys.executable, "-c", test_script],
                    capture_output=True,
                    text=True,
                    timeout=5
                )

                if result.returncode == 0:
                    # Test passed
                    actual = json.loads(result.stdout.strip())
                    results.append({
                        "passed": True,
                        "input": test_input,
                        "expected": expected,
                        "actual": actual
                    })
                    passed += 1
                else:
                    # Test failed
                    actual = "ERROR" if result.stderr else "MISMATCH"
                    results.append({
                        "passed": False,
                        "input": test_input,
                        "expected": expected,
                        "actual": actual
                    })
                    if not error and result.stderr:
                        error = result.stderr.split('\n')[0][:100]

            except subprocess.TimeoutExpired:
                error = "Time Limit Exceeded (5s)"
                results.append({
                    "passed": False,
                    "input": test_input,
                    "expected": expected,
                    "actual": "TIMEOUT"
                })
            except Exception as e:
                error = str(e)[:100]
                results.append({
                    "passed": False,
                    "input": test_input,
                    "expected": expected,
                    "actual": "ERROR"
                })

        return {
            "passed": passed,
            "total": len(test_cases),
            "results": results,
            "error": error
        }

    def _create_test_script(self, user_code: str, func_sig: str, test_input: Dict, expected: Any) -> str:
        """
        Create a safe test script that runs user code and compares output
        
        Args:
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
