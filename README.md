# APEX Code Solver RL Environment

**Stable Version 2.0** | OpenEnv-compliant | Production-ready with sandboxing, WebSockets, and procedural generation

A reinforcement learning environment for training agents to solve LeetCode-style coding problems. Agents receive problem statements with test cases, submit Python solutions, and receive rewards based on test case pass rates.

## Features

✅ **Multi-Session Management** - Parallel agents with isolated state via UUIDs  
✅ **Sandboxed Execution** - Subprocess isolation with resource limits (CPU, memory, processes)  
✅ **Security First** - AST-based code analysis to prevent dangerous imports/calls  
✅ **WebSocket Support** - Persistent connections for streaming test results  
✅ **Procedural Generation** - Infinite problem variants with seed control (7 templates)  
✅ **Typed Models** - Pydantic v2 schemas with OpenAPI docs  
✅ **Auto-Discovery** - `/manifest` endpoint for framework integration  
✅ **Reward Shaping** - Composite rewards (test pass rate + efficiency + attempt penalty)  
✅ **Scalable** - Docker Compose with nginx load balancer (3-8 replicas)  
✅ **HF Spaces** - Gradio interface for public deployment  

## Quick Start (5 Minutes)

### 1. Install

```bash
pip install -r requirements.txt
```

### 2. Start Server

```bash
python run_server.py
```

Visit `http://localhost:8000/docs` for interactive API documentation.

### 3. Use Client

```python
from envs.code_solver_env.client import CodeSolverClient

client = CodeSolverClient("http://localhost:8000", transport="http")

# Reset and get problem
reset = client.reset(difficulty="easy")
print(f"Problem: {reset['observation']['title']}")

# Submit solution
code = """def two_sum(nums, target):
    for i in range(len(nums)):
        for j in range(i+1, len(nums)):
            if nums[i] + nums[j] == target:
                return [i, j]
    return []"""

response = client.step(code)
print(f"Reward: {response['reward']:.2f}")
print(f"Passed: {response['observation']['passed_cases']}/{response['observation']['total_cases']}")
```

## Architecture

### Core Modules

- **models.py** - Pydantic v2 schemas (CodeAction, ProblemObservation, StepResponse, etc)
- **sandbox.py** - Subprocess execution with AST security checks
- **rewards.py** - Composite reward calculation (test pass + efficiency + penalties)
- **streaming.py** - SSE and WebSocket message builders
- **problems.py** - 9 canonical problems + ProceduralProblemGenerator (7 types)
- **code_solver_environment.py** - SessionManager + multi-session environment
- **server/app.py** - FastAPI with all endpoints (REST + WebSocket)
- **client.py** - Sync/async client for HTTP and WebSocket

### Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| POST | /reset | Start new episode, get problem |
| POST | /step | Execute code, get results |
| POST | /step/stream | Stream test results via SSE |
| GET | /state | Get session state |
| GET | /health | Health check |
| GET | /manifest | Environment specification |
| GET | /problems | List problems |
| GET | /problems/{id} | Get single problem |
| GET | /leaderboard | Top scores |
| GET | /sessions | Active sessions |
| DELETE | /sessions/{id} | Delete session |
| WS | /ws/{session_id} | WebSocket for persistent connection |

## Configuration

### Environment Variables

```bash
HOST=0.0.0.0              # Server host
PORT=8000                  # Server port
WORKERS=1                  # Number of worker processes
RELOAD=false               # Hot reload (dev only)
PYTHONUNBUFFERED=1         # Unbuffered output
```

### Session Settings

- **Timeout:** 30 minutes of inactivity
- **Max Steps:** 10 per episode
- **CPU Limit:** 10 seconds per execution
- **Memory Limit:** 256 MB per execution
- **File I/O:** Disabled (RLIMIT_FSIZE=0)
- **Subprocesses:** Disabled (RLIMIT_NPROC=1)

## Canonical Problems (9)

### Easy
1. **Two Sum** - Find pair that sums to target
2. **Palindrome Check** - Validate palindrome (ignoring non-alphanumeric)
3. **FizzBuzz** - Classic FizzBuzz problem

### Medium
4. **Longest Substring Without Repeating Characters**
5. **Valid Parentheses** - Bracket matching
6. **Maximum Subarray** - Kadane's algorithm

### Hard
7. **Merge K Sorted Lists** - Multi-list merge
8. **Trapping Rain Water** - Water volume calculation
9. **Word Break** - Dynamic programming

## Procedural Generation

Infinite problem variants via `ProceduralProblemGenerator`:

1. **Two Sum** - Randomize array size (10-1000), value range, duplicates
2. **Palindrome** - Randomize string length, character set
3. **Sorting** - Randomize array size, direction
4. **String Search** - Randomize pattern/text length, occurrence count
5. **Math** - Fibonacci/primes with parameter variations
6. **Tree** - Binary tree operations with random structures
7. **DP** - Coin change/knapsack with randomized weights

**Usage:**
```python
# Get procedural problem with fixed seed (deterministic)
reset = client.reset(mode="procedural", seed=42)

# Mix canonical and procedural (default)
reset = client.reset(mode="mixed")
```

## Reward System

### Primary (Test Pass Rate)
```
reward = passed_cases / total_cases
```

### Efficiency Bonus
```
+0.1 if all tests pass AND execution time < 2 seconds
-0.05 if all tests pass but execution time > 2 seconds
```

### Attempt Penalty
```
-0.02 * (step_count - 1)  # Encourage solving quickly
```

### Final Reward
```
final_reward = clamp(primary + efficiency + penalty, 0.0, 1.0)
```

## Security

### AST-Based Code Analysis

Blocked:
- Imports: `os`, `subprocess`, `socket`, `requests`, `__main__`, `ctypes`, etc.
- Built-ins: `eval`, `exec`, `compile`, `__import__`, `open`, `input`
- Dunder attributes: `__class__`, `__bases__`, etc.

### Resource Limits (Subprocess)

- **CPU Time:** 10 seconds max (RLIMIT_CPU)
- **Memory:** 256 MB max (RLIMIT_AS)
- **File Size:** 0 bytes (no file writes - RLIMIT_FSIZE)
- **Processes:** 1 max (no spawning - RLIMIT_NPROC)

### Execution Model

1. Parse code → AST security check
2. Create test harness (inject after user code)
3. Write to temp file
4. Execute in subprocess with limits
5. Parse JSON output with individual test results
6. Delete temp file in finally block

## Docker Deployment

### Development (3 Replicas + nginx)

```bash
docker-compose up
# Access: http://localhost:8000
```

### Production (8 Replicas, Resource Limits)

```bash
docker-compose -f docker-compose.scale.yml up
# 8 replicas × (2 CPU, 1GB RAM) with health checks
```

### nginx Load Balancer

- Upstream: Round-robin across replicas
- WebSocket: Persistent routing with 3600s timeouts
- SSE: Disabled buffering for streaming
- Health check: `/health` endpoint

## HuggingFace Spaces

Deploy to Spaces via `app_gradio.py`:

```bash
pip install -r requirements_hf.txt
python app_gradio.py
```

UI includes:
- **Try It Tab** - Problem selector, code editor, test results
- **API Docs Tab** - Embedded FastAPI documentation
- **Leaderboard Tab** - Top 10 scores
- **Problems Tab** - All canonical problems list

## Multi-Session Example

```python
import asyncio
from envs.code_solver_env.client import CodeSolverClient

async def solve_problem(client_transport="http"):
    client = CodeSolverClient("http://localhost:8000", transport=client_transport)
    
    # Define simple agent
    async def agent(obs):
        if obs["title"] == "Two Sum":
            return """def two_sum(nums, target):
    seen = {}
    for i, num in enumerate(nums):
        if target - num in seen:
            return [seen[target - num], i]
        seen[num] = i
    return []"""
        return "pass"
    
    # Run episode
    episode = await client.run_episode_async(agent, difficulty="easy", max_steps=5)
    print(f"Solved: {episode.best_reward == 1.0}")
    print(f"Steps: {episode.steps}")
    print(f"Best Reward: {episode.best_reward:.3f}")

asyncio.run(solve_problem())
```

## WebSocket Example

```python
import asyncio
import json
from envs.code_solver_env.client import CodeSolverClient

async def websocket_example():
    client = CodeSolverClient("ws://localhost:8000", transport="websocket")
    
    async with client:
        # Reset
        reset_resp = await client.reset_async(difficulty="easy")
        print(f"Problem: {reset_resp['observation']['title']}")
        
        # Step
        code = "def two_sum(nums, target):\n    return [0, 1]"
        step_resp = await client.step_async(code)
        print(f"Reward: {step_resp['reward']}")

asyncio.run(websocket_example())
```

## Testing

Run full test suite:

```bash
pytest test_suite.py -v
```

Tests cover:
- All 10 gaps (WebSocket, sessions, procedural, sandboxing, etc.)
- All endpoints (REST and WebSocket)
- Error handling and edge cases
- Reward calculation
- Problem generation

## Performance

**Benchmarks** (on i7-10700 with 16GB RAM):

- Health check: < 5ms
- Reset (canonical): ~10ms
- Reset (procedural): ~15ms
- Step (5 test cases): ~100ms
- Step (20 test cases): ~400ms

**Throughput:**

- Single server: ~50-100 steps/sec depending on test complexity
- 3-server (docker-compose): ~150-300 steps/sec
- 8-server (scale.yml): ~400-800 steps/sec

## Limitations & Known Issues

1. **In-Memory Sessions** - Restart loses all session data (use seeds for reproducibility)
2. **Single-Threaded Subprocess** - Steps run sequentially; consider async execution pool
3. **No Network** - Agents cannot access external APIs (by design)
4. **Linux/Mac Only** - Resource limits use POSIX only (Windows via WSL)

## Contributing

PRs welcome! Please:

1. Test against live server: `pytest test_suite.py`
2. Update docstrings for new endpoints
3. Add to Pydantic models if changing schemas
4. Test WebSocket with both transports

## Citation

```bibtex
@software{apex_code_solver,
  title={APEX Code Solver: RL Environment for Coding},
  version={2.0},
  url={https://github.com/...},
  year={2024}
}
```

## License

MIT - See LICENSE file

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
