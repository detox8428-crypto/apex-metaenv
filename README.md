# Code Solver RL Environment 🚀

**Code Solver** is a reinforcement learning environment for training AI agents to solve coding problems. Agents interact with LeetCode-style problems, submit Python solutions, and receive rewards based on test case passage rates.

## What is Code Solver?

Code Solver RL Environment is a production-ready training environment where agents learn to solve programming problems by writing and testing Python code. It provides objective, deterministic feedback through automated test case evaluation.

### Core Capabilities

✓ **LeetCode-style Problems** - 9 hand-crafted coding problems (easy/medium/hard)
✓ **Objective Grading** - Automated test case evaluation with pass/fail feedback
✓ **Partial Rewards** - Reward = (passed_cases / total_cases) for meaningful gradients
✓ **Deterministic** - Same code always produces same result
✓ **Pure Python** - Works in Docker, HF Spaces, minimal requirements (2vCPU/8GB)
✓ **OpenEnv Spec** - Standard reset/step/state interface
✓ **FastAPI Server** - REST API with interactive documentation
✓ **Scalable** - Easy to add more problems

## Quick Start (2 Minutes)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Start the Server
```bash
python run_server.py
```

Expected output:
```
Code Solver RL Environment
Starting FastAPI server...
Host: 0.0.0.0
Port: 8000

📖 Interactive docs: http://localhost:8000/docs
📖 Alternative docs: http://localhost:8000/redoc

Press CTRL+C to stop
```

### 3. Test with Client
```bash
python client_example.py
```

Or with curl:
```bash
# Health check
curl http://localhost:8000/health

# Reset (get a problem)
curl -X POST http://localhost:8000/reset

# Submit solution
curl -X POST http://localhost:8000/step \
  -H "Content-Type: application/json" \
  -d '{"action": {"code": "def twoSum(nums, target):\n    for i in range(len(nums)):\n        for j in range(i+1, len(nums)):\n            if nums[i] + nums[j] == target:\n                return [i, j]\n    return []"}}'
```

## Setup Instructions

### Docker Deployment

#### Option 1: Simple Docker Build
```bash
docker build -t apex-env .
docker run -p 8000:8000 apex-env
```

#### Option 2: Docker Compose
```bash
docker-compose up
```

## Coding Problems

The environment includes 9 LeetCode-style problems across 3 difficulty levels:

### Easy Problems
1. **Two Sum** - Find two numbers that add up to target
2. **Palindrome Check** - Check if string reads same forwards/backwards
3. **FizzBuzz** - Print numbers with FizzBuzz rules

### Medium Problems
4. **Longest Substring Without Repeating** - Find longest substring without duplicate characters
5. **Merge K Sorted Lists** - Merge multiple sorted linked lists
6. **LRU Cache** - Implement LRU cache with get/put operations

### Hard Problems
7. **Median of Two Sorted Arrays** - Find median of two sorted arrays
8. **Edit Distance** - Minimum edits to transform one string to another
9. **Regular Expression Matching** - Pattern matching with '.' and '*' wildcards

Each problem provides:
- Clear problem statement and examples
- Function signature to implement
- Constraints and edge cases
- 5-15 test cases for evaluation
- Difficulty rating

## REST API

### Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/health` | Server health check |
| POST | `/reset` | Reset environment, get new problem |
| POST | `/step` | Submit code solution |
| GET | `/state` | Get current problem state |
| GET | `/problems` | List all problems |

### POST /reset

Get a new random problem.

**Response:**
```json
{
  "observation": {
    "problem_id": "two_sum",
    "title": "Two Sum",
    "description": "Given an array of integers...",
    "function_signature": "def twoSum(nums: List[int], target: int) -> List[int]:",
    "examples": "Input: nums = [2,7,11,15], target = 9\nOutput: [0,1]",
    "constraints": "1 <= nums.length <= 10^5",
    "difficulty": "easy",
    "test_results": "Ready for submission",
    "passed_cases": 0,
    "total_cases": 10
  }
}
```

### POST /step

Submit Python code solution.

**Request:**
```json
{
  "action": {
    "code": "def twoSum(nums, target):\n    for i in range(len(nums)):\n        for j in range(i+1, len(nums)):\n            if nums[i] + nums[j] == target:\n                return [i, j]\n    return []"
  }
}
```

**Response:**
```json
{
  "observation": {...},
  "reward": 0.8,
  "terminated": false,
  "truncated": false,
  "info": {
    "passed_cases": 8,
    "total_cases": 10,
    "error_message": null
  }
}
```

**API Documentation**: http://localhost:8000/docs (Interactive Swagger UI)

## Python Client Usage

```python
import requests

# Client configuration
BASE_URL = "http://localhost:8000"

# 1. Reset environment - get a problem
response = requests.post(f"{BASE_URL}/reset")
observation = response.json()["observation"]

print(f"Problem: {observation['title']}")
print(f"Difficulty: {observation['difficulty']}")
print(f"Description: {observation['description']}")

# 2. Submit a solution
code = """
def twoSum(nums, target):
    seen = {}
    for i, num in enumerate(nums):
        if target - num in seen:
            return [seen[target - num], i]
        seen[num] = i
    return []
"""

response = requests.post(f"{BASE_URL}/step", json={"action": {"code": code}})
result = response.json()

print(f"Reward: {result['reward']:.2f}")
print(f"Passed: {result['info']['passed_cases']}/{result['info']['total_cases']}")

# 3. Check state
response = requests.get(f"{BASE_URL}/state")
state = response.json()
```

## Configuration

Code Solver is configured via `openenv.yaml`:

```yaml
server:
  host: "0.0.0.0"
  port: 8000
  debug: false

environment:
  num_problems: 9
  difficulty_distribution:
    easy: 3
    medium: 3
    hard: 3
  timeout_seconds: 10
  max_episode_steps: 10

code_execution:
  sandbox: true
  max_output_length: 10000
```

### Environment Variables

```bash
export API_BASE_URL="http://localhost:8000"
export MODEL_NAME="gpt-4"
export HF_TOKEN="your_huggingface_token"
export OPENAI_API_KEY="your_openai_key"
```

## Inference & Agent Integration

The `inference.py` module provides AI-powered code generation for solving problems:

```python
from inference import CodeSolverAgent

agent = CodeSolverAgent(model="gpt-4")

# Initialize episode
observation = agent.reset()

# Agent generates code based on problem
code = agent.generate_solution(observation)

# Submit and get feedback
result = agent.step(code)
reward = result['reward']

print(f"Test cases passed: {result['info']['passed_cases']}/{result['info']['total_cases']}")

# Continue if not all tests pass
if reward < 1.0:
    # Agent can revise based on feedback
    revised_code = agent.generate_solution(observation, feedback=result)
    result = agent.step(revised_code)
```

## Architecture

### OpenEnv Interface

Code Solver follows the OpenEnv specification:

- **reset()** - Start new episode with random problem
  - Returns: Observation with problem statement
  - Clears previous test results
  - Problem persists until next reset

- **step(action)** - Submit code solution
  - Input: Action with Python code
  - Returns: (observation, reward, terminated, truncated, info)
  - Observation: Updated problem state with test results
  - Reward: Float [0.0, 1.0] = passed_cases / total_cases
  - Terminated: True if all tests pass
  - Truncated: True if max_steps reached
  - Info: Test case details and error messages

### Observation Structure

```python
{
    "problem_id": str,          # Unique problem identifier
    "title": str,               # Problem name
    "description": str,         # Full problem statement
    "function_signature": str,  # Code template
    "examples": str,            # Input/output examples
    "constraints": str,         # Problem constraints
    "difficulty": str,          # "easy" | "medium" | "hard"
    "test_results": str,        # Detailed feedback
    "passed_cases": int,        # Number of passing tests
    "total_cases": int,         # Total test count
    "error_message": str        # Exception/syntax errors
}
```

### Reward System

Simple and deterministic:

```
reward = passed_cases / total_cases

Examples:
- 0/10 test cases = 0.0 reward
- 5/10 test cases = 0.5 reward
- 10/10 test cases = 1.0 reward (terminated=True)
```

### Project Structure

```
APEX-META/
├── run_server.py              # FastAPI server entry
├── server.py                  # Server implementation
├── inference.py               # AI-powered code generation
├── client_example.py          # Example client code
├── config.py                  # Configuration handling
├── requirements.txt           # Dependencies
├── openenv.yaml               # Environment config
├── Dockerfile                 # Container image
├── docker-compose.yml         # Multi-container setup
│
├── envs/
│   └── code_solver_env/       # Code solving environment
│       ├── server/
│       │   ├── app.py         # FastAPI routes
│       │   ├── code_solver_environment.py  # Core environment
│       │   └── problems.py    # Problem definitions
│       ├── client.py          # Client library
│       ├── models.py          # Data models
│       └── README.md          # Setup guide
│
└── [config files...]
```

## Troubleshooting

### Port Already in Use
```bash
python -c "import uvicorn; uvicorn.run('server:app', port=8001)"
```

### Import Errors
```bash
# Make sure you're in the right directory
cd c:\Users\bharu\OneDrive\Desktop\APEX-META
python run_server.py
```

### Missing Dependencies
```bash
pip install -r requirements.txt
```

### Code Execution Timeout
If a solution takes too long, increase the timeout in `openenv.yaml`:
```yaml
code_execution:
  timeout_seconds: 30  # Increase from 10
```

### Test Case Failures
Check `error_message` in the response:
- **SyntaxError**: Invalid Python syntax
- **NameError**: Missing function or variable
- **TypeError**: Wrong parameter types
- **AssertionError**: Test case failed

## Deployment

### Docker Deployment

**Option 1: Simple Docker Build**
```bash
docker build -t code-solver .
docker run -p 8000:8000 code-solver
```

**Option 2: Docker Compose**
```bash
docker-compose up
```

### Production Checklist

1. ✅ Install dependencies: `pip install -r requirements.txt`
2. ✅ Configure `openenv.yaml` with production settings
3. ✅ Set environment variables for inference (OPENAI_API_KEY, HF_TOKEN)
4. ✅ Start server: `python run_server.py`
5. ✅ Verify API: http://localhost:8000/health
6. ✅ Access docs: http://localhost:8000/docs

---

✅ **Status**: Production Ready
**Version**: 2.0.0 (Code Solver RL Environment)
**OpenEnv Spec**: Compliant
