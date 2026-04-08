#!/usr/bin/env python3
"""
APEX OpenEnv Hackathon - Inference Script
Runs LLM agent against the local APEX environment
"""

import os
import sys
import json
import traceback
import requests
from openai import OpenAI

# ============================================================
# ENV VARS
# ============================================================
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")
API_KEY = os.getenv("HF_TOKEN") or os.getenv("API_KEY")

# Local environment server
LOCAL_ENV_URL = "http://localhost:8000"

# ============================================================
# LOGGING FUNCTIONS - exact format required by judges
# ============================================================

def log_start(task, env, model):
    """Log task start."""
    print(f"[START] task={task} env={env} model={model}", flush=True)

def log_step(step, action, reward, done, error):
    """Log step result."""
    action_str = str(action)[:100].replace('\n', ' ')
    error_str = f"{error}" if error else "null"
    print(f"[STEP] step={step} action={action_str!r} reward={reward:.2f} done={done} error={error_str}", flush=True)

def log_end(success, steps, score, rewards):
    """Log episode end."""
    rewards_str = ",".join([f"{r:.2f}" for r in rewards])
    print(f"[END] success={success} steps={steps} score={score:.2f} rewards={rewards_str}", flush=True)

# ============================================================
# OPENAI CLIENT
# ============================================================

client = OpenAI(
    base_url=API_BASE_URL,
    api_key=API_KEY or "dummy"
)

SYSTEM_PROMPT = """You are an expert Python engineer. 
Your task is to write a complete Python function called `solve(problem)` that solves the given problem.
Return ONLY valid Python code, no explanations."""

TASKS = [
    "solve-easy",
    "solve-medium",
    "solve-hard",
]

MAX_STEPS = 8
SUCCESS_THRESHOLD = 0.5

def get_agent_action(problem_desc, feedback="", step=1):
    """Get LLM response for current problem."""
    user_msg = f"""Problem: {problem_desc}"""
    if feedback:
        user_msg += f"\n\nPrevious feedback: {feedback}\nImprove your code based on this feedback."
    
    user_msg += "\n\nWrite a complete Python function called `solve(problem)` that solves this. Return ONLY the code."

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_msg}
            ],
            max_tokens=1000,
            temperature=0.3,
            timeout=30
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"def solve(problem):\n    return None  # Error: {str(e)}"

def run_task(task_name):
    """Run one task against the local APEX environment."""
    env_name = "apex"
    
    # Determine difficulty from task name
    if "easy" in task_name:
        difficulty = "easy"
    elif "medium" in task_name:
        difficulty = "medium"
    else:
        difficulty = "hard"
    
    log_start(task=task_name, env=env_name, model=MODEL_NAME)
    
    rewards = []
    feedback = ""
    steps_taken = 0
    success = False
    error_occurred = False
    
    try:
        # Reset the environment
        try:
            reset_resp = requests.post(
                f"{LOCAL_ENV_URL}/reset",
                json={"difficulty": difficulty},
                timeout=30
            )
            reset_resp.raise_for_status()
            reset_data = reset_resp.json()
        except Exception as e:
            log_step(step=1, action="reset_failed", reward=0.0, done=True, error=str(e))
            log_end(success=False, steps=0, score=0.0, rewards=[])
            return 0.0
        
        session_id = reset_data.get("session_id")
        problem_state = reset_data.get("state", {})
        problem_desc = problem_state.get("problem", "")
        
        # Run the task loop
        for step in range(1, MAX_STEPS + 1):
            try:
                # Get agent action
                action = get_agent_action(problem_desc, feedback, step)
                
                # Submit step to environment
                try:
                    step_resp = requests.post(
                        f"{LOCAL_ENV_URL}/step",
                        json={
                            "session_id": session_id,
                            "action": {"code": action}
                        },
                        timeout=30
                    )
                    step_resp.raise_for_status()
                    result = step_resp.json()
                except Exception as e:
                    log_step(step=step, action=action, reward=0.0, done=True, error=str(e))
                    error_occurred = True
                    break
                
                reward = float(result.get("reward", 0.0))
                terminated = bool(result.get("terminated", False))
                feedback = result.get("feedback", "")
                
                rewards.append(reward)
                steps_taken = step
                
                log_step(step=step, action=action, reward=reward, done=terminated, error=None)
                
                if terminated:
                    break
                
                # Update problem state for next step if available
                if result.get("state"):
                    problem_state = result["state"]
                    problem_desc = problem_state.get("problem", problem_desc)
            
            except Exception as e:
                log_step(step=step, action="error", reward=0.0, done=True, error=str(e))
                error_occurred = True
                break
        
        # Calculate score
        score = max(rewards) if rewards else 0.0
        success = score >= SUCCESS_THRESHOLD
    
    except Exception as e:
        # Outer exception handler
        error_occurred = True
        log_step(step=1, action="error", reward=0.0, done=True, error=str(e))
    
    finally:
        # Always log end, even if an exception occurred
        score = max(rewards) if rewards else 0.0
        log_end(success=success, steps=steps_taken, score=score, rewards=rewards)
        print(flush=True)
    
    return score

def main():
    """Run the benchmark."""
    try:
        print("=" * 80, flush=True)
        print("APEX OPENENVIRONMENT BENCHMARK", flush=True)
        print(f"Model: {MODEL_NAME}", flush=True)
        print(f"API Base URL: {API_BASE_URL}", flush=True)
        print(f"Local Env URL: {LOCAL_ENV_URL}", flush=True)
        print("=" * 80, flush=True)
        print(flush=True)
        
        all_scores = []
        
        for task in TASKS:
            score = run_task(task)
            all_scores.append(score)
        
        avg = sum(all_scores) / len(all_scores) if all_scores else 0.0
        
        print("=" * 80, flush=True)
        print("BENCHMARK SUMMARY", flush=True)
        print("=" * 80, flush=True)
        print(f"Tasks completed: {len(all_scores)}/{len(TASKS)}", flush=True)
        print(f"Average score: {avg:.2f}", flush=True)
        print("=" * 80, flush=True)
        
    except Exception as e:
        print(f"[ERROR] Benchmark failed: {e}", flush=True)
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
