import os
import sys
import asyncio
import requests
from openai import OpenAI

# ── Environment variables ────────────────────────────────────────────────────
API_BASE_URL = os.getenv("API_BASE_URL", "https://api.openai.com/v1")
MODEL_NAME   = os.getenv("MODEL_NAME", "gpt-4o-mini")
HF_TOKEN     = os.getenv("HF_TOKEN")

if HF_TOKEN is None:
    raise ValueError("HF_TOKEN environment variable is required")

# ── Config ───────────────────────────────────────────────────────────────────
SPACE_URL    = os.getenv("SPACE_URL", "https://shaikb-apex.hf.space")
BENCHMARK    = "apex-engineering-benchmark"
MAX_STEPS    = 3
TEMPERATURE  = 0.2
MAX_TOKENS   = 1024

TASKS = [
    {"task": "easy-solve-001",  "domain": "data_pipeline",  "difficulty": "easy"},
    {"task": "medium-solve-001","domain": "data_pipeline",  "difficulty": "medium"},
    {"task": "hard-solve-001",  "domain": "data_pipeline",  "difficulty": "hard"},
    {"task": "cr-easy-001",     "domain": "code_review",    "difficulty": "easy"},
    {"task": "cr-medium-001",   "domain": "code_review",    "difficulty": "medium"},
    {"task": "cr-hard-001",     "domain": "code_review",    "difficulty": "hard"},
    {"task": "id-easy-001",     "domain": "incident_debug", "difficulty": "easy"},
    {"task": "id-medium-001",   "domain": "incident_debug", "difficulty": "medium"},
    {"task": "id-hard-001",     "domain": "incident_debug", "difficulty": "hard"},
]

SYSTEM_PROMPT = """You are an expert software engineer and SRE.
For data pipeline tasks: write a Python solve(df) function using pandas only.
For code review tasks: identify the bug, explain its production impact, and provide a fix.
For incident debug tasks: identify the root cause, explain the cascade, and give a prevention strategy.
Be concise and precise. Output only the solution, no preamble."""


def log_start(task: str, model: str):
    print(f"[START] task={task} env={BENCHMARK} model={model}", flush=True)


def log_step(step: int, action: str, reward: float, done: bool, error):
    action_safe = action.replace("\n", "\\n")[:120]
    err = "null" if error is None else str(error)
    done_str = "true" if done else "false"
    print(f"[STEP]  step={step} action={action_safe!r} reward={reward:.2f} done={done_str} error={err}", flush=True)


def log_end(success: bool, steps: int, rewards: list):
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    success_str = "true" if success else "false"
    print(f"[END]   success={success_str} steps={steps} rewards={rewards_str}", flush=True)

def call_env(method: str, path: str, **kwargs):
    url = f"{SPACE_URL}{path}"
    resp = requests.request(method, url, timeout=30, **kwargs)
    resp.raise_for_status()
    return resp.json()


def get_agent_action(client: OpenAI, observation: dict) -> str:
    domain = observation.get("domain", "")
    desc   = observation.get("description", "")
    sample = observation.get("data_sample", "")
    code   = observation.get("code_to_review", "")
    log    = observation.get("incident_log", "")
    fback  = observation.get("feedback", "")

    parts = [f"Task: {desc}"]
    if sample: parts.append(f"Data:\n{sample}")
    if code:   parts.append(f"Code to review:\n{code}")
    if log:    parts.append(f"Incident log so far:\n{log}")
    if fback:  parts.append(f"Previous feedback: {fback}")

    user_prompt = "\n\n".join(parts)

    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": user_prompt},
            ],
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
        )
        return (completion.choices[0].message.content or "").strip() or "no solution"
    except Exception as exc:
        print(f"[DEBUG] LLM call failed: {exc}", flush=True)
        return "no solution"


def build_action(domain: str, agent_text: str) -> dict:
    if domain == "data_pipeline":
        return {"code": agent_text}
    elif domain == "code_review":
        return {"review": agent_text}
    else:
        return {"diagnosis": agent_text}


def run_episode(client: OpenAI, task_info: dict) -> None:
    task_id  = task_info["task"]
    domain   = task_info["domain"]
    difficulty = task_info["difficulty"]

    rewards   = []
    steps_done = 0
    success   = False

    log_start(task=task_id, model=MODEL_NAME)

    try:
        # ── reset ────────────────────────────────────────────────────────────
        reset_resp = call_env(
            "POST", "/reset",
            json={"domain": domain, "difficulty": difficulty},
        )
        session_id  = reset_resp.get("session_id", "")
        observation = reset_resp.get("observation", reset_resp)
        done        = observation.get("done", False)

        # ── steps ─────────────────────────────────────────────────────────────
        for step in range(1, MAX_STEPS + 1):
            if done:
                break

            agent_text = get_agent_action(client, observation)
            action_body = build_action(domain, agent_text)
            action_body["session_id"] = session_id

            step_resp = call_env("POST", "/step", json=action_body)

            reward = float(step_resp.get("reward", 0.0))
            done   = bool(step_resp.get("done", False))
            error  = step_resp.get("error", None)
            observation = step_resp.get("observation", {})

            rewards.append(reward)
            steps_done = step
            log_step(step=step, action=agent_text, reward=reward, done=done, error=error)

        # ── score ─────────────────────────────────────────────────────────────
        avg_reward = sum(rewards) / len(rewards) if rewards else 0.0
        success = avg_reward >= 0.5

    except Exception as exc:
        print(f"[DEBUG] Episode error: {exc}", flush=True)
        if not rewards:
            rewards = [0.0]
            steps_done = 0

    finally:
        # cleanup session
        try:
            call_env("DELETE", f"/sessions/{session_id}")
        except Exception:
            pass
        log_end(success=success, steps=steps_done, rewards=rewards)


def main():
    client = OpenAI(base_url=API_BASE_URL, api_key=HF_TOKEN)
    for task_info in TASKS:
        run_episode(client, task_info)


if __name__ == "__main__":
    main()
