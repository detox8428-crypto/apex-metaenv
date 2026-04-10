#!/usr/bin/env python3
"""
APEX OpenEnv Hackathon - Inference Script
Runs LLM agent against the APEX environment
"""

import os
import sys
import json
import traceback
import requests
from openai import OpenAI

# ============================================================
# ENV VARS — validator injects these, NO fallback defaults
# ============================================================
API_BASE_URL = os.environ["API_BASE_URL"]
API_KEY = os.environ["API_KEY"]
MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")
ENV_URL = os.environ.get("ENV_URL", "https://shaikb-apex.hf.space")

# ============================================================
# OPENAI CLIENT — must use injected base_url and api_key
# ============================================================
client = OpenAI(
    base_url=API_BASE_URL,
    api_key=API_KEY,
)

# ============================================================
# LOGGING — exact format required by judges, do not change
# ============================================================
def log_start(task, env, model):
    print(f"[START] task={task} env={env} model={model}", flush=True)

def log_step(step, action, reward, done, error):
    action_str = str(action)[:80].replace('\n', ' ')
    done_str = "true" if done else "false"
    error_str = str(error) if error else "null"
    print(f"[STEP] step={step} action={action_str!r} reward={reward:.2f} done={done_str} error={error_str}", flush=True)

def log_end(success, steps, score, rewards):
    success_str = "true" if success else "false"
    rewards_str = ",".join([f"{r:.2f}" for r in rewards])
    print(f"[END] success={success_str} steps={steps} score={score:.2f} rewards={rewards_str}", flush=True)

# ============================================================
# TASKS
# ============================================================
TASKS = [
    {"name": "email-easy",    "type": "email",   "difficulty": "easy"},
    {"name": "meeting-medium","type": "meeting",  "difficulty": "medium"},
    {"name": "workflow-hard", "type": "workflow", "difficulty": "hard"},
]

MAX_STEPS = 6
SUCCESS_THRESHOLD = 0.5

SYSTEM_PROMPT = """You are an AI assistant controlling a productivity environment.
You will be given the current state of the environment and must output a JSON action.
Return ONLY a valid JSON object, no explanation, no markdown."""

def get_llm_action(task_type, observation_text, feedback="", step=1):
    """Call LLM via the injected API proxy to get next action."""
    if task_type == "email":
        user_msg = f"""Current environment state:
{observation_text}

Output a JSON action to send an email. Use this exact format:
{{"action_type": "email", "recipient_id": 1, "subject": "Hello", "body": "Your email body here", "priority": "MEDIUM", "language": "EN"}}"""
    elif task_type == "meeting":
        user_msg = f"""Current environment state:
{observation_text}

Output a JSON action to schedule a meeting. Use this exact format:
{{"action_type": "meeting", "title": "Team Sync", "attendee_ids": [1, 2], "scheduled_time": "2024-12-01T10:00:00", "duration_minutes": 60, "meeting_type": "VIRTUAL"}}"""
    else:
        user_msg = f"""Current environment state:
{observation_text}

Output a JSON action to complete the workflow. Use this exact format:
{{"action_type": "noop", "reason": "Processing workflow step {step}"}}"""

    if feedback:
        user_msg += f"\n\nPrevious feedback: {feedback}"

    # This call MUST go through API_BASE_URL — do not catch exceptions here
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_msg}
        ],
        max_tokens=500,
        temperature=0.3,
    )
    return response.choices[0].message.content.strip()

def run_task(task_config):
    """Run one full task episode."""
    task_name = task_config["name"]
    task_type = task_config["type"]

    log_start(task=task_name, env="apex", model=MODEL_NAME)

    rewards = []
    steps_taken = 0
    success = False
    score = 0.0

    try:
        # Reset environment
        reset_resp = requests.post(
            f"{ENV_URL}/reset",
            json={"seed": 42, "max_episode_steps": MAX_STEPS},
            timeout=30
        )
        reset_resp.raise_for_status()
        reset_data = reset_resp.json()
        observation = str(reset_data.get("initial_observation", ""))

        feedback = ""
        for step in range(1, MAX_STEPS + 1):
            # Get LLM action — no try/except so API call is visible to validator
            raw_action = get_llm_action(task_type, observation, feedback, step)

            # Parse JSON action
            try:
                action_dict = json.loads(raw_action)
            except Exception:
                # If JSON parse fails, use a safe noop
                action_dict = {"action_type": "noop", "reason": "parse_error"}

            # Submit to environment
            try:
                step_resp = requests.post(
                    f"{ENV_URL}/step",
                    json={"action": action_dict},
                    timeout=30
                )
                step_resp.raise_for_status()
                result = step_resp.json()
            except Exception as e:
                log_step(step=step, action=action_dict, reward=0.0, done=True, error=str(e))
                break

            reward = float(result.get("reward", 0.0))
            done = bool(result.get("done", False))
            feedback = str(result.get("info", {}).get("feedback", ""))
            observation = str(result.get("observation", observation))

            rewards.append(reward)
            steps_taken = step

            log_step(step=step, action=action_dict, reward=reward, done=done, error=None)

            if done:
                break

        score = max(rewards) if rewards else 0.0
        success = score >= SUCCESS_THRESHOLD

    except Exception as e:
        log_step(step=max(steps_taken, 1), action="error", reward=0.0, done=True, error=str(e))

    finally:
        score = max(rewards) if rewards else 0.0
        log_end(success=success, steps=steps_taken, score=score, rewards=rewards)

    return score


def main():
    print(f"[INFO] APEX Benchmark starting", flush=True)
    print(f"[INFO] Model: {MODEL_NAME}", flush=True)
    print(f"[INFO] API Base: {API_BASE_URL}", flush=True)
    print(f"[INFO] Env URL: {ENV_URL}", flush=True)

    all_scores = []
    for task in TASKS:
        score = run_task(task)
        all_scores.append(score)

    avg = sum(all_scores) / len(all_scores) if all_scores else 0.0
    print(f"[INFO] Average score: {avg:.2f}", flush=True)


if __name__ == "__main__":
    main()
