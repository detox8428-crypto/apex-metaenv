# Screen Task Environment (screen_task_env)

OpenEnv Environment for GUI Interaction Learning inspired by Peekaboo. An AI agent learns to interact with a Windows GUI (Notepad) by observing screenshots and executing actions in response to natural language task descriptions.

## Overview

**Purpose**: Train reinforcement learning agents to understand and interact with computer screens in response to natural language instructions.

**Concept**: 
- Agent receives a screenshot of Notepad and a natural language task
- Agent produces an action (click, type, hotkey, or submit)
- Environment executes the action and returns:
  - New screenshot
  - Task description
  - Action feedback
  - Reward (1.0 if task completed, 0.0 otherwise)
  - Episode done flag

## Environment Specification

### Actions

1. **click** - Click at screen coordinates
   - `x` (int): X coordinate
   - `y` (int): Y coordinate

2. **type** - Type text into focused element
   - `text` (str): Text to type

3. **hotkey** - Press keyboard shortcut
   - `keys` (str): Key combination (e.g., "ctrl+a", "ctrl+c")

4. **submit** - Signal task completion

### Observations

```python
{
    "screenshot_b64": str,        # Current screen (base64 PNG)
    "task": str,                  # Natural language task
    "last_action_result": str,    # Action feedback
    "step_num": int               # Current step (0-50)
}
```

### Reward

- `1.0`: Task completed successfully
- `0.0`: Action performed but task not yet complete
- **Max steps per episode**: 50

### Tasks (10 provided)

1. Type "Python"
2. Type "Hello World"
3. Type numbers 1-10 (one per line)
4. Write a haiku about programming
5. Type "OpenEnv Challenge"
6. Type name and date (Name - YYYY-MM-DD)
7. List 5 programming languages
8. Type "AI Agent Learning"
9. Type "RL Environment"
10. Type "Hackathon 2026"

## Installation

### Prerequisites
- Python 3.9+
- Windows OS (for Notepad automation)
- pip

### Setup

1. Navigate to the environment directory:
```bash
cd envs/screen_task_env
```

2. Install dependencies:
```bash
pip install -e .
```

Or manually:
```bash
pip install fastapi uvicorn pydantic requests pyautogui mss Pillow pyperclip
```

## Quick Start

### 1. Start the Server

```bash
cd envs\screen_task_env
python -m uvicorn server.app:app --host 0.0.0.0 --port 8000 --reload
```

Expected output:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 2. Run Test Client

Create a test script `test_client.py`:

```python
import time
import base64
from io import BytesIO
from PIL import Image
from screen_task_env.client import ScreenTaskEnvClient
from screen_task_env.models import ScreenAction

# Connect to server
client = ScreenTaskEnvClient("http://localhost:8000")

# Reset environment - get initial screenshot and task
print("Resetting environment...")
obs = client.reset()
print(f"Task: {obs.task}")
print(f"Step: {obs.step_num}")

# Example: Type the required text
action = ScreenAction(
    action_type="type",
    text="Hello World"
)

print("\nExecution action: type 'Hello World'...")
obs, reward, done = client.step(action)
print(f"Reward: {reward}")
print(f"Done: {done}")
print(f"Result: {obs.last_action_result}")

if done:
    print("✓ Task completed!")
else:
    print("Task not yet complete. Try more actions...")

# Optional: Save screenshot for inspection
if obs.screenshot_b64:
    try:
        img_data = base64.b64decode(obs.screenshot_b64)
        img = Image.open(BytesIO(img_data))
        img.save("screenshot.png")
        print("Screenshot saved to screenshot.png")
    except:
        pass

client.close()
```

### 3. Run the Test

```bash
python test_client.py
```

### Complete Example (Agent Loop)

```python
from screen_task_env.client import ScreenTaskEnvClient
from screen_task_env.models import ScreenAction
import time

client = ScreenTaskEnvClient("http://localhost:8000")

# Reset and get task
observation = client.reset()
print(f"Task: {observation.task}")

done = False
step = 0

# Simple agent that types all actions
actions_to_take = [
    ScreenAction(action_type="type", text="Hello World"),
    ScreenAction(action_type="submit")
]

for action in actions_to_take:
    observation, reward, done = client.step(action)
    step += 1
    print(f"Step {step}: Reward={reward}, Done={done}")
    
    if done:
        print("Task completed!")
        break
    
    time.sleep(0.2)

client.close()
```

## Architecture

```
screen_task_env/
├── __init__.py                    # Package init
├── models.py                      # Data models (Action, Observation, State)
├── client.py                      # HTTP client for agents
├── openenv.yaml                   # Environment specification
├── pyproject.toml                 # Dependencies
├── Dockerfile                     # Container image
├── README.md                      # This file
└── server/
    ├── __init__.py
    ├── app.py                     # FastAPI server
    ├── screen_task_environment.py # Core environment logic
    └── tasks.py                   # Task definitions
```

## Key Implementation Details

### Success Checking
Determines task completion by:
1. Selecting all text in Notepad (Ctrl+A)
2. Copying to clipboard (Ctrl+C)
3. Checking if required substring is present

### Screenshot Capture
- Uses MSS library for efficient screen capture
- Returns base64-encoded PNG for transmission

### Action Execution
- **Click**: Uses `pyautogui.click(x, y)`
- **Type**: Uses `pyautogui.typewrite(text)`
- **Hotkey**: Parses key combinations like "ctrl+a" and executes

### Safety Features
- Maximum 50 steps per episode
- Automatic Notepad process management
- Configurable timeouts and delays

## Extending the Environment

### Adding New Tasks

Edit `server/tasks.py`:

```python
TASKS.append({
    "task_id": "task_011",
    "description": "Your new task description",
    "app": "Notepad",
    "success_check": "notepad_text_contains:required_text",
    "difficulty": "easy"  # easy, medium, hard
})
```

### Modifying Rewards

Edit `server/screen_task_environment.py`, in `step()`:

```python
# Custom reward function
reward = 1.0 if success else -0.01 * self.step_count
```

### Using Different Applications

Replace Notepad with another app:
1. Update `reset()` to launch different executable
2. Update `_check_success()` to validate against that app's text
3. Update task definitions

## Troubleshooting

### Server won't start
- Check port 8000 is not in use: `netstat -ano | findstr :8000`
- Kill: `taskkill /PID <pid> /F`

### Notepad automation fails
- Ensure Notepad windows aren't hidden/minimized
- Add `time.sleep(0.5)` delays if actions are too fast
- Check pyautogui/mss installation: `pip install --upgrade pyautogui mss`

### Screenshots are blank
- Verify monitor detection in `_capture_screenshot()`
- Check Multi-monitor setup (`self.sct.monitors`)

## Performance Notes

- **Typical episode**: 3-10 steps to completion
- **Action latency**: ~300ms (capture + execution)
- **Screenshot size**: ~500KB base64 encoded
- **Recommended batch size**: 1 episode at a time for desktop

## OpenEnv Compliance

- ✓ Implements `reset()` → Observation
- ✓ Implements `step(Action)` → (Observation, Reward, Done)
- ✓ Sparse reward (0.0 or 1.0)
- ✓ FastAPI server on port 8000
- ✓ HTTP client for remote agents
- ✓ Base64 image observations

## License

MIT

.
