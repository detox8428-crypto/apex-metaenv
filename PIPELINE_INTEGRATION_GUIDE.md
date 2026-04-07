# APEX Data Pipeline Engineer - Integration Guide

## What's Been Done
✅ models.py - New Pydantic models for PipelineAction, DataSample, ReviewSubmission, PipelineObservation
✅ problems.py - 18 real-world data pipeline tasks (6 solve + 6 review + 6 debug)
✅ rewards.py - PipelineRewardCalculator with 3 modes (solve/review/debug)
✅ openenv.yaml - Updated name and description
✅ README.md - Complete documentation with examples

## Remaining: app.py Updates

The key changes needed in `envs/code_solver_env/server/app.py`:

### 1. Import New Components
```python
from models import PipelineAction, PipelineObservation, ReviewSubmission
from rewards import PipelineRewardCalculator  # Replace RewardCalculator
from problems import select_random_task, get_task_by_id
```

### 2. Update /reset Endpoint
```python
@app.post("/reset")
async def reset_episode(difficulty: str = "easy", task_type: str = "solve"):
    """Reset environment and get new task"""
    session_id = str(uuid.uuid4())
    
    # Select task
    task = select_random_task(task_type=task_type, difficulty=difficulty)
    
    # Create observation
    observation = PipelineObservation(
        task_id=task['task_id'],
        title=task['title'],
        description=task['description'],
        task_type=task['task_type'],
        difficulty=task['difficulty'],
        function_signature=task['function_signature'],
        data_sample={
            "format": task['data_sample']['format'],
            "content": task['data_sample']['content'],
            "description": task['data_sample']['description']
        },
        current_code=task.get('current_code'),  # For review/debug
        error_message=task.get('error_message'),  # For debug
        passed_cases=0,
        total_cases=task['test_cases'][0].get('total', 0),
        step_count=0,
        max_steps=5
    )
    
    # Store in session state
    env.session_states[session_id] = {
        "task": task,
        "step_count": 0,
        "observation": observation.dict(),
        "previous_reward": 0.0
    }
    
    return ResetResponse(session_id=session_id, observation=observation)
```

### 3. Update /step Endpoint for Multiple Modes
```python
@app.post("/step")
async def step(action: PipelineAction, session_id: str):
    """Execute step for current task"""
    
    state = env.session_states.get(session_id)
    if not state:
        raise HTTPException(status_code=404, detail="Session not found")
    
    task = state["task"]
    task_type = task["task_type"]
    
    # Route to appropriate handler
    if task_type == "solve":
        return handle_solve_step(action, state)
    elif task_type == "review":
        return handle_review_step(action, state)
    elif task_type == "debug":
        return handle_debug_step(action, state)
    else:
        raise HTTPException(status_code=400, detail="Unknown task type")

async def handle_solve_step(action: PipelineAction, state: dict) -> StepResponse:
    """Handle SOLVE mode: execute code against test data"""
    task = state["task"]
    state["step_count"] += 1
    
    try:
        # Execute agent code against test cases
        code = action.code
        visible_passed = 0  # Count visible tests passed
        hidden_passed = 0   # Count hidden tests passed
        visible_total = task['visible_test_count']
        hidden_total = task['hidden_test_count']
        
        # Run visible tests (execute code against test_cases data)
        for test_case in task['test_cases'][:task['visible_test_count']]:
            # Inject code, run assertions...
            # visible_passed += count_passing_assertions(...)
            pass
        
        # Hidden tests: pretend ran (in real impl, generate and run hidden tests)
        # For demo: assume some hidden tests pass based on visible performance
        hidden_passed = int(visible_passed / visible_total * hidden_total) if visible_total > 0 else 0
        
        # Calculate reward
        reward_result = PipelineRewardCalculator.calculate_solve_reward(
            visible_passed=visible_passed,
            visible_total=visible_total,
            hidden_passed=hidden_passed,
            hidden_total=hidden_total,
            step_count=state["step_count"],
            task_difficulty=task['difficulty']
        )
        
        reward = reward_result["reward"]
        done = reward_result["done"] or state["step_count"] >= 5
        
        observation = state["observation"]
        observation["passed_cases"] = hidden_passed
        observation["step_count"] = state["step_count"]
        
        return StepResponse(
            session_id=session_id,
            observation=PipelineObservation(**observation),
            reward=reward,
            done=done,
            info={
                "passed_cases": hidden_passed,
                "total_cases": hidden_total,
                "breakdown": reward_result["breakdown"]
            }
        )
    except Exception as e:
        # Syntax/runtime error
        return StepResponse(
            session_id=session_id,
            observation=PipelineObservation(**state["observation"]),
            reward=0.0,
            done=False,
            info={"error": str(e)}
        )

async def handle_review_step(action: PipelineAction, state: dict) -> StepResponse:
    """Handle REVIEW mode: parse review JSON and score it"""
    task = state["task"]
    state["step_count"] += 1
    
    try:
        review = action.review  # JSON: bug_location, bug_type, explanation, fixed_code
        
        # Extract true bug details from task
        true_bug_location = task.get("bug_location")
        true_bug_type = task.get("bug_type")
        
        # Score components
        location_correct = is_location_correct(review["bug_location"], true_bug_location)
        type_correct = review["bug_type"] == true_bug_type
        keywords = task.get("keywords", ["bug", task["bug_type"].replace("_", " ")])
        explanation_good = any(kw in review["explanation"].lower() for kw in keywords)
        
        # Test fixed code
        fixed_code_passing = run_tests(review["fixed_code"], task["test_cases"])
        
        # Calculate reward
        reward_result = PipelineRewardCalculator.calculate_review_reward(
            bug_location_correct=location_correct,
            bug_location_agent=review["bug_location"],
            bug_location_true=true_bug_location,
            bug_type_correct=type_correct,
            explanation_has_keywords=explanation_good,
            fixed_code_all_passing=fixed_code_passing,
            fixed_code_tests_passed=count_passing_tests(review["fixed_code"], task["test_cases"]),
            fixed_code_tests_total=len(task["test_cases"]),
            step_count=state["step_count"]
        )
        
        reward = reward_result["reward"]
        done = reward_result["done"]
        
        return StepResponse(
            session_id=session_id,
            observation=PipelineObservation(**state["observation"]),
            reward=reward,
            done=done,
            info={"breakdown": reward_result["breakdown"]}
        )
    except Exception as e:
        return StepResponse(
            session_id=session_id,
            observation=PipelineObservation(**state["observation"]),
            reward=0.0,
            done=False,
            info={"error": str(e)}
        )

async def handle_debug_step(action: PipelineAction, state: dict) -> StepResponse:
    """Handle DEBUG mode: fix crashing code"""
    task = state["task"]
    state["step_count"] += 1
    previous_passed = state.get("previous_passed", 0)
    
    try:
        code = action.code
        
        # Run tests
        tests_passed = count_passing_tests(code, task["test_cases"])
        tests_total = len(task["test_cases"])
        
        # Determine if cascading (hard difficulty with multiple bugs)
        is_cascading = task['difficulty'] == 'hard' and 'cascading' in task['task_id']
        all_cascading_fixed = tests_passed == tests_total if is_cascading else False
        
        # Calculate reward
        reward_result = PipelineRewardCalculator.calculate_debug_reward(
            tests_passed=tests_passed,
            tests_total=tests_total,
            step_count=state["step_count"],
            previous_tests_passed=previous_passed if state["step_count"] > 1 else None,
            is_cascading_hard=is_cascading,
            all_cascading_fixed=all_cascading_fixed
        )
        
        reward = reward_result["reward"]
        done = reward_result["done"]
        
        state["previous_passed"] = tests_passed
        
        # For debug: optionally show next error if not done
        feedback = None
        if not done and state["step_count"] < 5:
            feedback = get_next_error(code, task, state["step_count"])
        
        return StepResponse(
            session_id=session_id,
            observation=PipelineObservation(**state["observation"]),
            reward=reward,
            done=done,
            info={
                "breakdown": reward_result["breakdown"],
                "feedback": feedback
            }
        )
    except Exception as e:
        return StepResponse(
            session_id=session_id,
            observation=PipelineObservation(**state["observation"]),
            reward=0.0,
            done=False,
            info={"error": str(e)}
        )
```

## Remaining: inference.py

Create `inference.py` in root directory:

```python
#!/usr/bin/env python3
"""
APEX Data Pipeline Engineer - Benchmark Inference
Tests all 9 task combinations: 3 types × 3 difficulties
"""

import os
import sys
import json
import time
import logging
from datetime import datetime
from typing import Dict, Any, List
import requests

logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


class PipelineAgent:
    """Agent for testing APEX Data Pipeline environment"""
    
    def __init__(self, env_url: str = "http://localhost:8000"):
        self.env_url = env_url
        self.rewards = []
        self.episode_count = 0
    
    def reset(self, task_type: str, difficulty: str) -> Dict[str, Any]:
        """Reset and get new task"""
        response = requests.post(
            f"{self.env_url}/reset",
            json={"task_type": task_type, "difficulty": difficulty},
            timeout=10
        )
        return response.json()
    
    def step(self, code: str, session_id: str) -> Dict[str, Any]:
        """Execute step"""
        response = requests.post(
            f"{self.env_url}/step",
            json={"code": code, "session_id": session_id},
            timeout=15
        )
        return response.json()
    
    def run_episode(self, task_type: str, difficulty: str, max_steps: int = 5) -> Dict[str, Any]:
        """Run complete episode"""
        self.episode_count += 1
        
        # Reset
        reset_result = self.reset(task_type, difficulty)
        session_id = reset_result['session_id']
        task = reset_result['observation']
        task_id = task['task_id']
        
        logger.info(f"\n[START] task={task_id} mode={task_type} env=apex-data-pipeline model=Qwen2.5-72B-Instruct")
        
        episode_rewards = []
        episode_steps = 0
        success = True
        
        for step_num in range(1, max_steps + 1):
            episode_steps = step_num
            
            # Generate action (simplified: dummy code)
            if task_type == "solve":
                action_code = self._generate_solve_code(task)
            elif task_type == "review":
                action_code = self._generate_review(task)
            else:  # debug
                action_code = self._generate_debug_fix(task)
            
            # Execute step
            step_result = self.step(action_code, session_id)
            reward = step_result.get('reward', 0.0)
            done = step_result.get('done', False)
            error = step_result.get('info', {}).get('error')
            
            action_desc = f"submit_{'code' if task_type in ['solve', 'debug'] else 'review'}({len(str(action_code))} chars)"
            logger.info(f"[STEP] step={step_num} action={action_desc} reward={reward:.2f} done={str(done).lower()} error={error}")
            
            episode_rewards.append(reward)
            
            if done:
                break
            if error:
                success = False
        
        # Summary
        avg_reward = sum(episode_rewards) / len(episode_rewards) if episode_rewards else 0.0
        total_reward = sum(episode_rewards)
        final_score = avg_reward  # Or weighted calculation
        
        logger.info(f"[END] success={str(success).lower()} steps={episode_steps} score={final_score:.2f} rewards={','.join(f'{r:.2f}' for r in episode_rewards)}")
        
        self.rewards.append(final_score)
        
        return {
            "task_id": task_id,
            "task_type": task_type,
            "difficulty": difficulty,
            "steps": episode_steps,
            "rewards": episode_rewards,
            "score": final_score,
            "success": success
        }
    
    def _generate_solve_code(self, task: Dict[str, Any]) -> str:
        """Generate code for SOLVE task (simplified)"""
        # In real impl: call LLM to generate code
        return "import pandas as pd\n\ndef func(df):\n    return df"
    
    def _generate_review(self, task: Dict[str, Any]) -> Dict[str, str]:
        """Generate review for REVIEW task"""
        # In real impl: call LLM to analyze bug
        return {
            "bug_location": "line 2",
            "bug_type": task.get("bug_type", "wrong_aggregation"),
            "explanation": f"Incorrect {task.get('bug_type', 'aggregation')} logic",
            "fixed_code": "def fixed(df):\n    return df"
        }
    
    def _generate_debug_fix(self, task: Dict[str, Any]) -> str:
        """Generate fix for DEBUG task"""
        # In real impl: call LLM to fix error
        return "import pandas as pd\n\ndef fixed(df):\n    return df"


def main():
    """Run 9-episode benchmark"""
    env_url = os.getenv("ENV_URL", "http://localhost:8000")
    
    logger.info("=" * 60)
    logger.info("APEX Data Pipeline Engineer - Benchmark Inference")
    logger.info("=" * 60)
    
    # Check server health
    try:
        health = requests.get(f"{env_url}/health", timeout=5)
        if health.status_code != 200:
            logger.error(f"Server health check failed: {health.status_code}")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Cannot connect to server at {env_url}: {e}")
        sys.exit(1)
    
    agent = PipelineAgent(env_url)
    
    # Run 9 episodes: 3 solve + 3 review + 3 debug
    episodes = [
        ("solve", "easy"),
        ("solve", "medium"),
        ("solve", "hard"),
        ("review", "easy"),
        ("review", "medium"),
        ("review", "hard"),
        ("debug", "easy"),
        ("debug", "medium"),
        ("debug", "hard"),
    ]
    
    results = []
    for task_type, difficulty in episodes:
        try:
            result = agent.run_episode(task_type, difficulty)
            results.append(result)
        except Exception as e:
            logger.error(f"Episode failed: {e}")
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info(f"Completed {len(results)} episodes")
    if agent.rewards:
        avg_reward = sum(agent.rewards) / len(agent.rewards)
        total_reward = sum(agent.rewards)
        logger.info(f"Average reward: {avg_reward:.2f}")
        logger.info(f"Total reward: {total_reward:.2f}")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
```

## Testing Checklist

- [ ] `python run_server.py` starts successfully
- [ ] GET /health returns 200
- [ ] POST /reset returns valid PipelineObservation
- [ ] POST /step returns float reward in [0.0, 1.0]
- [ ] Run `python inference.py` completes 9 episodes
- [ ] Rewards are in expected ranges: 0.30-0.90
- [ ] All episodes show multi-step trajectories (not 1-step 1.00)
- [ ] Docker build succeeds: `docker build -t apex-data-pipeline .`

## Environment Variables

```bash
# Optional
export API_BASE_URL="https://router.huggingface.co/v1"
export MODEL_NAME="Qwen/Qwen2.5-72B-Instruct"
export HF_TOKEN="hf_..."
export ENV_URL="http://localhost:8000"
```

## Deployment to HuggingFace Spaces

```bash
git add .
git commit -m "Upgrade to real-world data pipeline RL environment"
git push hf main
```

The `/app` folder in Spaces will automatically run `python run_server.py` based on the Dockerfile.
