#!/usr/bin/env python3
"""
APEX Engineering Benchmark - Inference Script
Runs LLM agent against the APEX environment
"""

import os
import asyncio
import requests
from openai import OpenAI

# ============================================================
# REQUIRED ENV VARS (do not add defaults to HF_TOKEN)
# ============================================================
API_BASE_URL = os.getenv("API_BASE_URL", "https://shaikb-apex.hf.space")
MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")
HF_TOKEN = os.getenv("HF_TOKEN")

# Optional - for local docker image testing
LOCAL_IMAGE_NAME = os.getenv("LOCAL_IMAGE_NAME")

# ============================================================
# LOGGING FUNCTIONS - exact format required by judges
# ============================================================

def log_start(task, env, model):
    print(f"[START] task={task} env={env} model={model}", flush=True)

def log_step(step, action, reward, done, error):
    action_str = str(action)[:80].replace('\n', ' ')
    print(f"[STEP] step={step} action={action_str!r} reward={reward:.4f} done={done} error={error}", flush=True)

def log_end(success, steps, score, rewards):
    print(f"[END] success={success} steps={steps} score={score:.4f} rewards={rewards}", flush=True)

# ============================================================
# OPENAI CLIENT - uses env vars
# ============================================================

client = OpenAI(
    base_url="https://api-inference.huggingface.co/v1",
    api_key=HF_TOKEN or "dummy"
)

SYSTEM_PROMPT = """You are a senior software engineer and SRE expert.
For data_pipeline tasks: write a complete Python function called solve(df) using pandas.
For code_review tasks: identify the exact bug AND explain production impact 
  - you MUST mention: scale, users affected, timeout, data loss, latency.
For incident_debug tasks: diagnose root cause, explain the cascade, provide fix.
Read feedback carefully after each step and improve your answer."""

EPISODES = [
    {"domain": "data_pipeline",  "difficulty": "easy",   "task_id": "dp-easy-001"},
    {"domain": "data_pipeline",  "difficulty": "medium", "task_id": "dp-medium-001"},
    {"domain": "data_pipeline",  "difficulty": "hard",   "task_id": "dp-hard-001"},
    {"domain": "code_review",    "difficulty": "easy",   "task_id": "cr-easy-001"},
    {"domain": "code_review",    "difficulty": "medium", "task_id": "cr-medium-001"},
    {"domain": "code_review",    "difficulty": "hard",   "task_id": "cr-hard-001"},
    {"domain": "incident_debug", "difficulty": "easy",   "task_id": "id-easy-001"},
    {"domain": "incident_debug", "difficulty": "medium", "task_id": "id-medium-001"},
    {"domain": "incident_debug", "difficulty": "hard",   "task_id": "id-hard-001"},
]

MAX_STEPS = 3
SUCCESS_THRESHOLD = 0.5
MAX_TOTAL_REWARD = MAX_STEPS * len(EPISODES)

def get_agent_action(observation, feedback="", step=1):
    """Get LLM response for current observation."""
    domain = observation.get("domain", "data_pipeline")
    
    user_msg = f"""Task: {observation.get('title', '')}
Description: {observation.get('description', '')}
"""
    if observation.get("data_sample"):
        user_msg += f"\nData:\n{observation['data_sample']}\n"
    if observation.get("code_to_review"):
        user_msg += f"\nCode to review:\n{observation['code_to_review']}\n"
    if observation.get("logs"):
        user_msg += f"\nLogs:\n{observation['logs']}\n"
    if feedback:
        user_msg += f"\nPrevious feedback: {feedback}\nImprove your answer now."

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_msg}
            ],
            max_tokens=500,
            temperature=0.3
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"def solve(df):\n    return df  # Error: {e}"

def run_episode(domain, difficulty, task_id):
    """Run one episode against the APEX environment."""
    env_name = "apex-engineering-benchmark"
    
    # Reset
    try:
        r = requests.post(
            f"{API_BASE_URL}/reset",
            json={"domain": domain, "difficulty": difficulty},
            timeout=30
        )
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        log_start(task=task_id, env=env_name, model=MODEL_NAME)
        log_step(step=1, action="reset_failed", reward=0.0, done=True, error=str(e))
        log_end(success=False, steps=0, score=0.0, rewards=[])
        return 0.0

    session_id = data["session_id"]
    observation = data["observation"]

    log_start(task=task_id, env=env_name, model=MODEL_NAME)

    rewards = []
    feedback = ""
    steps_taken = 0

    for step in range(1, MAX_STEPS + 1):
        # Get agent action
        action = get_agent_action(observation, feedback, step)

        # Build action payload
        if domain == "data_pipeline":
            payload = {"session_id": session_id, "code": action}
        elif domain == "code_review":
            payload = {"session_id": session_id, "review": action}
        else:
            payload = {"session_id": session_id, "diagnosis": action}

        # Submit step
        try:
            r = requests.post(
                f"{API_BASE_URL}/step",
                json=payload,
                timeout=30
            )
            r.raise_for_status()
            result = r.json()
        except Exception as e:
            log_step(step=step, action=action, reward=0.0, done=True, error=str(e))
            break

        reward = float(result.get("reward", 0.0))
        done = bool(result.get("done", False))
        feedback = result.get("feedback", "")
        error = None

        rewards.append(reward)
        steps_taken = step

        log_step(step=step, action=action, reward=reward, done=done, error=error)

        if done:
            break

        # Update observation for next step
        if result.get("observation"):
            observation = result["observation"]

    score = sum(rewards) / MAX_TOTAL_REWARD if MAX_TOTAL_REWARD > 0 else 0.0
    score = min(max(score, 0.0), 1.0)
    success = max(rewards) >= SUCCESS_THRESHOLD if rewards else False

    log_end(success=success, steps=steps_taken, score=score, rewards=rewards)
    print(flush=True)

    return max(rewards) if rewards else 0.0


def main():
    print("=" * 80, flush=True)
    print("APEX ENGINEERING BENCHMARK v3.0", flush=True)
    print(f"Model: {MODEL_NAME}", flush=True)
    print(f"Environment: {API_BASE_URL}", flush=True)
    print("=" * 80, flush=True)
    print(flush=True)

    all_scores = []
    domain_scores = {}

    for ep in EPISODES:
        score = run_episode(ep["domain"], ep["difficulty"], ep["task_id"])
        all_scores.append(score)
        domain_scores.setdefault(ep["domain"], []).append(score)

    avg = sum(all_scores) / len(all_scores) if all_scores else 0.0

    print("=" * 80, flush=True)
    print("BENCHMARK SUMMARY", flush=True)
    print("=" * 80, flush=True)
    print(f"Episodes completed: {len(all_scores)}/{len(EPISODES)}", flush=True)
    print(f"Average reward: {avg:.4f}", flush=True)
    print(flush=True)
    print("Per-Domain Performance:", flush=True)
    for domain, scores in domain_scores.items():
        davg = sum(scores) / len(scores)
        print(f"  {domain:<20} -> avg={davg:.4f} ({len(scores)} episodes)", flush=True)
    print("=" * 80, flush=True)


if __name__ == "__main__":
    main()
