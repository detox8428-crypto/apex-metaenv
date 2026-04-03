# Code Solver Environment

OpenEnv environment for training RL agents to **solve coding problems** by writing and testing Python code — a real-world production task.

## Why This Wins

✅ **Real-world task** — AI code generation/solving is production work  
✅ **Objective grading** — Test cases pass or fail, no ambiguity  
✅ **Partial rewards** — Agents get meaningful gradients (X/N test cases passed)  
✅ **Deterministic** — Same code = same result every time  
✅ **Pure Python** — Works in Docker, HF Spaces, 2vCPU/8GB RAM  
✅ **Scalable** — Easy to add more coding problems  
✅ **LeetCode-style** — Familiar problem format to agents  

## Quick Start

### 1. Install

```bash
cd envs/code_solver_env
pip install -e .
```

### 2. Run Server

```bash
python -m uvicorn server.app:app --reload --port 8000
```

### 3. Test with curl

```bash
# Health check
curl http://localhost:8000/health

# Reset (get a random problem)
curl -X POST http://localhost:8000/reset

# Submit code
curl -X POST http://localhost:8000/step \
  -H "Content-Type: application/json" \
  -d '{"action": {"code": "def twoSum(nums, target):\n    for i in range(len(nums)):\n        for j in range(i+1, len(nums)):\n            if nums[i] + nums[j] == target:\n                return [i, j]\n        return []"}}'
```

### 4. Run Inference Agent

```bash
cd ../..
python inference.py
```

## Environment Spec

### Actions

Agent submits Python code:

```python
class CodeSolverAction:
    code: str  # Complete Python function
```

### Observations

Problem statement + test results:

```python
class CodeSolverObservation:
    problem_id: str              # Unique ID
    title: str                   # Problem name
    description: str             # Problem statement
    function_signature: str      # Required signature
    examples: str                # Input/output examples
    constraints: str             # Problem constraints
    difficulty: str              # easy/medium/hard
    test_results: str            # Feedback
    passed_cases: int            # Number passed
    total_cases: int             # Total test cases
    error_message: str           # Syntax/runtime error
```

### Reward

Partial reward based on test case pass rate:

```
reward = passed_cases / total_cases
```

Range: 0.0 (no tests pass) → 1.0 (all tests pass)

### Problems (9 total)

**Easy (3):**
- Two Sum
- Palindrome Check
- FizzBuzz

**Medium (3):**
- Longest Substring Without Repeating
- Valid Parentheses
- Maximum Subarray (Kadane's)

**Hard (3):**
- Merge K Sorted Lists
- Trapping Rain Water
- Word Break

## Judging Criteria

| Weight | Criterion | Your Score |
|--------|-----------|-----------|
| 30% | Real-world task | ✅ AI code solving is production work |
| 25% | Agent quality | Depends on your LLM |
| 20% | Code quality | ✅ Clean, secure subprocess execution |
| 15% | Novel/creativity | ✅ First OpenEnv code solver |
| 10% | Performance | ✅ <100ms/test, <20min total, 2vCPU ready |

## Safety

- **Never uses `eval()` or `exec()`** in main process
- **Always runs agent code in subprocess** with 5s timeout
- **Safe handling** of syntax errors, runtime errors, infinite loops
- **Deterministic grading** — test cases define correctness

## File Structure

```
code_solver_env/
├── __init__.py
├── models.py             # Pydantic models
├── client.py             # HTTP client
├── openenv.yaml          # Spec
├── pyproject.toml        # Dependencies
├── Dockerfile            # Container
├── README.md
└── server/
    ├── __init__.py
    ├── app.py            # FastAPI
    ├── code_solver_environment.py  # Core logic
    └── problems.py       # 9 coding problems
```

## Extending

### Add More Problems

Edit `server/problems.py`:

```python
PROBLEMS.append({
    "problem_id": "p010",
    "title": "New Problem",
    "difficulty": "medium",
    "description": "...",
    "function_signature": "def solution(...):",
    "examples": "Example 1: ...",
    "constraints": "...",
    "test_cases": [
        {"input": {"arg1": val1}, "expected": result1},
        ...
    ],
    "solution_template": "def solution(...):\n    pass"
})
```

### Change Reward Function

Edit `CodeSolverEnvironment.step()`:

```python
# Current: linear (X/N)
# Can add: exponential, weighted by difficulty, bonus for first-try, etc.
reward = passed / total if total > 0 else 0.0
```

## License

MIT
