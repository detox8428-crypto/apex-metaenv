---
title: APEX Code Solver RL Environment
emoji: 🤖
colorFrom: blue
colorTo: purple
sdk: gradio
sdk_version: 4.x
app_file: app_gradio.py
pinned: false
---

# APEX Code Solver on HuggingFace Spaces

Interactive web interface for the APEX Code Solver RL environment using Gradio.

## What Is This?

An interactive coding problem solver interface where you can:
- Load LeetCode-style problems (9 canonical + infinite procedural variants)
- Write Python solutions in a code editor
- See real-time test results with pass/fail indicators
- Track your best performance on a live leaderboard
- Browse all available problems

## How to Use

### 1. Load a Problem

1. Go to the **Try It** tab
2. Select difficulty: Easy, Medium, or Hard
3. Click **Load New Problem**
4. You'll see:
   - Problem title
   - Detailed description
   - Function signature (what to implement)
   - Example test cases
   - Constraints (array size, value range, time complexity hints)

### 2. Write Your Solution

1. Click in the **Code Editor** (left side)
2. Write your Python function inside the template
3. Don't modify the function signature or test harness

**Example Solution:**
```python
def two_sum(nums, target):
    """Find two numbers that sum to target."""
    seen = {}
    for i, num in enumerate(nums):
        complement = target - num
        if complement in seen:
            return [seen[complement], i]
        seen[num] = i
    return []
```

### 3. Submit and See Results

1. Click the **Submit** button
2. Wait 2-5 seconds for test execution
3. See results:
   - Green checkmarks = test case passed
   - Red X = test case failed
   - Execution time for each test
   - Overall reward (0.0 to 1.0)

### 4. View Leaderboard

- Go to **Leaderboard** tab
- See top 10 scores for each problem
- Sort by score, timestamp
- Your session appears with timestamp

### 5. Browse Problems

- Go to **Problems** tab
- View all 9 canonical problems
- See difficulty, test case count, and type
- Click problem ID to load that specific problem

## Available Problems

### Easy (3)
- **Two Sum** - Find pair of numbers that sum to target
- **Palindrome Check** - Validate if string is palindrome (ignoring non-alphanumeric)
- **FizzBuzz** - Classic FizzBuzz implementation

### Medium (3)
- **Longest Substring** - Find longest substring without repeating characters
- **Valid Parentheses** - Check if brackets are properly matched
- **Maximum Subarray** - Find contiguous subarray with largest sum

### Hard (3)
- **Merge K Sorted Lists** - Merge multiple sorted lists efficiently
- **Trapping Rain Water** - Calculate water trapped after rainfall
- **Word Break** - Determine if string can be segmented into dictionary words

## Procedural Generation

Beyond the 9 canonical problems, the backend can generate **infinite variants** with different parameters:

- **Two Sum variants:** Different array sizes (10-1000), value ranges, duplicate handling
- **String problems:** Varying lengths, character sets, pattern distributions
- **Tree problems:** Different tree structures, sizes, node values
- **DP problems:** Varying knapsack capacities, coin denominations

Each variant is deterministic (same seed = same problem).

## How Grading Works

Your code is graded on:

1. **Test Case Passage** - What % of test cases pass?
2. **Execution Speed** - Solved under 2 seconds? (+0.1 bonus)
3. **Attempt Efficiency** - Did you solve it quickly or take many attempts? (penalty per step)

**Reward Calculation:**
```
reward = (passed_cases / total_cases) + efficiency_bonus - attempt_penalty
reward = clamp(reward, 0.0, 1.0)  # Between 0 and 1
```

**Examples:**
- 4/5 tests pass, lots of attempts → ~0.6 reward
- 5/5 tests pass, under 2s, 1 attempt → 1.0 reward
- 5/5 tests pass, 5 seconds, 3 attempts → ~0.8 reward

## Constraints & Execution Model

**Security:**
- Your code runs in an isolated subprocess (can't access files or network)
- Forbidden: `import os`, `import subprocess`, `eval()`, `exec()`, `open()`
- Timeout: 10 seconds max per execution
- Memory: 256 MB max per execution

**What's Tested:**
- 5-20 hidden test cases per problem
- Examples shown are a subset of actual tests
- Your grades on examples don't count—only hidden tests matter

## API Endpoints

This Spaces instance runs a backend server. Advanced users can call the API directly:

```bash
# Get problem
curl -X GET "http://localhost:7860/api/reset?difficulty=easy"

# Submit code
curl -X POST "http://localhost:7860/api/step" \
  -H "Content-Type: application/json" \
  -d '{"code": "...", "session_id": "..."}'

# Get leaderboard
curl -X GET "http://localhost:7860/api/leaderboard"
```

See **API Docs** tab in the interface for full endpoint documentation.

## WebSocket (Advanced)

For persistent connections:

```javascript
const ws = new WebSocket("ws://localhost:7860/ws/session-123");

ws.onopen = () => {
  ws.send(JSON.stringify({
    "type": "reset",
    "difficulty": "medium"
  }));
};

ws.onmessage = (event) => {
  const msg = JSON.parse(event.data);
  console.log(msg);
};
```

## Performance Notes

- **Fresh page load:** 2-3 seconds
- **Problem load:** 1-2 seconds
- **Code submission:** 2-5 seconds (depends on test complexity)
- **Leaderboard refresh:** 1 second

## Limitations

1. **Session Timeout** - Your session expires after 30 minutes of inactivity
2. **Memory Limits** - Large data structure operations may hit 256 MB limit
3. **No Persistence** - Page refresh creates new session (use session_id parameter)
4. **Rate Limiting** - Not currently implemented (use responsibly)

## Troubleshooting

### "Error: No active session"
- Click "Load New Problem" from the dropdown
- The interface creates a new session automatically

### Timeout Error
- Your code took >10 seconds to execute
- Look for inefficient loops or large data structures
- Consider optimization (e.g., hash table instead of nested loops)

### Security Error
- You tried to import a forbidden module or call eval()
- Check: os, subprocess, socket, http, requests, open, eval, exec
- These are blocked to keep execution safe

### Memory Error
- Your solution used >256 MB of memory
- Reduce data structure sizes or use more efficient algorithms
- Example: avoid creating huge intermediate lists

## Local Development

To run locally:

```bash
# Install deps
pip install -r requirements_hf.txt

# Run
python app_gradio.py

# Access at http://localhost:7860
```

## Citation

```bibtex
@software{apex_code_solver_2024,
  title={APEX Code Solver: RL Environment for Coding},
  version={2.0},
  url={https://huggingface.co/spaces/...},
  year={2024}
}
```

## Feedback

Found a bug? Have a feature request? 

- Check existing problem statement for clarity
- Verify your solution meets all constraints
- For infrastructure issues, report on main repo

---

**Built with FastAPI + Gradio + Pydantic**  
Open source MIT license
