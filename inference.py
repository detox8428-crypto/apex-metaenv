import os
import requests
from openai import OpenAI

# ── Env vars ─────────────────────────────────────────────────────────────────
API_BASE_URL = os.getenv("API_BASE_URL", "https://api.openai.com/v1")
MODEL_NAME   = os.getenv("MODEL_NAME", "gpt-4o-mini")
HF_TOKEN     = os.getenv("HF_TOKEN")
SPACE_URL    = os.getenv("SPACE_URL", "https://shaikb-apex.hf.space")

if HF_TOKEN is None:
    raise ValueError("HF_TOKEN environment variable is required")

BENCHMARK  = "apex-engineering-benchmark"
MAX_STEPS  = 3
TEMP       = 0.2
MAX_TOKENS = 1024

TASKS = [
    {"task_id": "easy-solve-001",  "domain": "data_pipeline",  "difficulty": "easy"},
    {"task_id": "medium-solve-001","domain": "data_pipeline",  "difficulty": "medium"},
    {"task_id": "hard-solve-001",  "domain": "data_pipeline",  "difficulty": "hard"},
    {"task_id": "cr-easy-001",     "domain": "code_review",    "difficulty": "easy"},
    {"task_id": "cr-medium-001",   "domain": "code_review",    "difficulty": "medium"},
    {"task_id": "cr-hard-001",     "domain": "code_review",    "difficulty": "hard"},
    {"task_id": "id-easy-001",     "domain": "incident_debug", "difficulty": "easy"},
    {"task_id": "id-medium-001",   "domain": "incident_debug", "difficulty": "medium"},
    {"task_id": "id-hard-001",     "domain": "incident_debug", "difficulty": "hard"},
]

SYSTEM = (
    "You are a senior software engineer and SRE.\n"
    "For data_pipeline: write a Python solve(df) function using pandas.\n"
    "For code_review: identify the bug, explain production impact, give fix.\n"
    "For incident_debug: identify root cause, explain cascade, give fix + prevention.\n"
    "Be concise. Output only the solution."
)


def log_start(task: str, model: str):
    print(f"[START] task={task} env={BENCHMARK} model={model}", flush=True)


def log_step(step: int, action: str, reward: float, done: bool, error):
    a = repr(action.replace("\n", "\\n")[:100])
    d = "true" if done else "false"
    e = "null" if error is None else str(error)
    print(f"[STEP]  step={step} action={a} reward={reward:.2f} done={d} error={e}", flush=True)


def log_end(success: bool, steps: int, rewards: list):
    s = "true" if success else "false"
    r = ",".join(f"{x:.2f}" for x in rewards)
    print(f"[END]   success={s} steps={steps} rewards={r}", flush=True)


def call(method, path, **kw):
    url = f"{SPACE_URL}{path}"
    r = requests.request(method, url, timeout=30, **kw)
    r.raise_for_status()
    return r.json()


def agent(client, obs: dict, domain: str) -> str:
    desc  = obs.get("description", "")
    data  = obs.get("data_sample", "")
    code  = obs.get("code_to_review", "")
    log   = obs.get("incident_log", "")
    fb    = obs.get("feedback", "")
    parts = [f"Task: {desc}"]
    if data: parts.append(f"Data:\n{data}")
    if code: parts.append(f"Code:\n{code}")
    if log:  parts.append(f"Logs so far:\n{log}")
    if fb:   parts.append(f"Previous feedback: {fb}")
    try:
        resp = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role":"system","content":SYSTEM},
                      {"role":"user","content":"\n\n".join(parts)}],
            temperature=TEMP, max_tokens=MAX_TOKENS,
        )
        return (resp.choices[0].message.content or "").strip() or "no answer"
    except Exception as exc:
        print(f"[DEBUG] LLM error: {exc}", flush=True)
        return "no answer"


def action_body(domain: str, session_id: str, text: str) -> dict:
    key = {"data_pipeline":"code","code_review":"review","incident_debug":"diagnosis"}[domain]
    return {"session_id": session_id, key: text}


def run_task(client, task: dict):
    task_id    = task["task_id"]
    domain     = task["domain"]
    difficulty = task["difficulty"]
    rewards    = []
    steps      = 0
    success    = False
    session_id = None

    log_start(task=task_id, model=MODEL_NAME)
    try:
        # reset
        res        = call("POST", "/reset", json={"domain": domain, "difficulty": difficulty})
        session_id = res.get("session_id", "")
        obs        = res.get("observation", res)
        done       = obs.get("done", False) if isinstance(obs, dict) else False

        for step in range(1, MAX_STEPS + 1):
            if done:
                break
            text  = agent(client, obs if isinstance(obs, dict) else {}, domain)
            body  = action_body(domain, session_id, text)
            step_r = call("POST", "/step", json=body)
            reward = float(step_r.get("reward", 0.0))
            done   = bool(step_r.get("done", False))
            error  = step_r.get("error", None)
            obs    = step_r.get("observation", {})
            rewards.append(reward)
            steps = step
            log_step(step=step, action=text, reward=reward, done=done, error=error)

        avg = sum(rewards) / len(rewards) if rewards else 0.0
        success = avg >= 0.5

    except Exception as exc:
        print(f"[DEBUG] task {task_id} error: {exc}", flush=True)
        if not rewards:
            rewards = [0.0]
    finally:
        if session_id:
            try: call("DELETE", f"/sessions/{session_id}")
            except Exception: pass
        log_end(success=success, steps=steps, rewards=rewards)


def main():
    client = OpenAI(base_url=API_BASE_URL, api_key=HF_TOKEN)
    for task in TASKS:
        run_task(client, task)


if __name__ == "__main__":
    main()
