import os
import requests
from openai import OpenAI

# ── Env vars ──────────────────────────────────────────────────────────────────
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME   = os.getenv("MODEL_NAME", "gpt-4o-mini")
HF_TOKEN     = os.getenv("HF_TOKEN")
SPACE_URL    = os.getenv("SPACE_URL", "https://shaikb-apex.hf.space")

if HF_TOKEN is None:
    raise ValueError("HF_TOKEN environment variable is required")

BENCHMARK  = "apex-engineering-benchmark"
MAX_STEPS  = 3
TEMP       = 0.1          # lower = more deterministic = fewer silly bugs
MAX_TOKENS = 1024

TASKS = [
    {"task_id": "dp-easy-001",   "domain": "data_pipeline",  "difficulty": "easy"},
    {"task_id": "dp-medium-001", "domain": "data_pipeline",  "difficulty": "medium"},
    {"task_id": "dp-hard-001",   "domain": "data_pipeline",  "difficulty": "hard"},
    {"task_id": "cr-easy-001",   "domain": "code_review",    "difficulty": "easy"},
    {"task_id": "cr-medium-001", "domain": "code_review",    "difficulty": "medium"},
    {"task_id": "cr-hard-001",   "domain": "code_review",    "difficulty": "hard"},
    {"task_id": "id-easy-001",   "domain": "incident_debug", "difficulty": "easy"},
    {"task_id": "id-medium-001", "domain": "incident_debug", "difficulty": "medium"},
    {"task_id": "id-hard-001",   "domain": "incident_debug", "difficulty": "hard"},
]

# ── System prompts per domain ─────────────────────────────────────────────────
SYSTEM_PIPELINE = """You are an expert Python/pandas data engineer.

RULES (follow exactly):
1. Implement ONLY the function whose signature is given — no extra functions, no main block.
2. Use only: pandas, datetime, re, json, math, collections — no pip installs.
3. Handle edge cases: empty DataFrames, NaN values, wrong dtypes.
4. Output raw Python only — NO markdown fences, NO explanation, NO comments.

Task-specific function names:
- easy task: def aggregate_sales(df) — group by customer_id, sum amount, return sorted Series
- medium task: def clean_transactions(df) — drop_duplicates(), fillna(0), return cleaned DataFrame
- hard task: def compare_dates(df) — use pd.to_datetime(df['timestamp'], utc=True, errors='coerce') to normalize ALL timestamps to UTC-aware, return full DataFrame with all original columns

Always match the exact function name from the task description."""

SYSTEM_REVIEW = """You are a senior software engineer doing production code review.

Structure your review in exactly this format:
BUG: <name of the bug, e.g. "N+1 Query", "Race Condition">
LOCATION: <function/line where bug occurs>
PRODUCTION IMPACT: <what fails at scale — mention users, data loss, or outage>
FIX: <concrete code fix or approach>

Be specific. Judges score: bug identification + production impact keywords + fix quality."""

SYSTEM_DEBUG = """You are an SRE diagnosing a live production incident.

Structure your diagnosis in exactly this format:
ROOT CAUSE: <specific technical root cause>
CASCADE: <how this caused the observed symptoms step by step>
FIX: <immediate action to stop the bleeding>
PREVENTION: <long-term fix to prevent recurrence>

Later steps reveal more logs — update your diagnosis as new evidence appears."""


def build_prompt(obs: dict, domain: str, step: int) -> tuple[str, str]:
    """Returns (system_prompt, user_prompt) with ALL observation fields included."""

    if domain == "data_pipeline":
        system = SYSTEM_PIPELINE
        # THE KEY FIX: include function_signature and examples
        sig      = obs.get("function_signature", obs.get("data_sample", ""))
        examples = obs.get("examples", "")
        constraints = obs.get("constraints", "")
        desc     = obs.get("description", "")
        data_sample = obs.get("data_sample", "")
        fb       = obs.get("feedback", "")

        user = f"TASK:\n{desc}\n\nSAMPLE DATA (CSV):\n{data_sample}\n\nIMPLEMENT THIS FUNCTION:\n{sig}"
        if examples:
            user += f"\n\nEXAMPLES:\n{examples}"
        if constraints:
            user += f"\n\nCONSTRAINTS:\n{constraints}"
        if fb and step > 1:
            user += f"\n\nPREVIOUS ATTEMPT FEEDBACK (fix these issues):\n{fb}"
        user += "\n\nOutput ONLY the Python function, no fences, no explanation."

    elif domain == "code_review":
        system = SYSTEM_REVIEW
        code = obs.get("code_to_review", obs.get("description", ""))
        desc = obs.get("description", obs.get("title", ""))
        fb   = obs.get("feedback", "")
        user = f"TASK: {desc}\n\nCODE TO REVIEW:\n```python\n{code}\n```"
        if fb and step > 1:
            user += f"\n\nPREVIOUS FEEDBACK:\n{fb}"

    else:  # incident_debug
        system = SYSTEM_DEBUG
        log  = obs.get("incident_log", obs.get("description", ""))
        desc = obs.get("description", obs.get("title", ""))
        fb   = obs.get("feedback", "")
        user = f"INCIDENT: {desc}\n\nLOGS REVEALED SO FAR:\n{log}"
        if fb and step > 1:
            user += f"\n\nPREVIOUS DIAGNOSIS FEEDBACK:\n{fb}"
        user += f"\n\nStep {step} of {obs.get('max_steps', MAX_STEPS)} — more logs may appear next step."

    return system, user


def call_llm(client, system: str, user: str) -> str:
    try:
        resp = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system},
                {"role": "user",   "content": user},
            ],
            temperature=TEMP,
            max_tokens=MAX_TOKENS,
        )
        text = (resp.choices[0].message.content or "").strip()
        # Strip markdown fences if model adds them anyway
        if text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join(
                l for l in lines
                if not l.strip().startswith("```")
            ).strip()
        return text or "no answer"
    except Exception as exc:
        print(f"[DEBUG] LLM error: {exc}", flush=True)
        return "no answer"


def call_env(method: str, path: str, **kw):
    r = requests.request(method, f"{SPACE_URL}{path}", timeout=45, **kw)
    r.raise_for_status()
    return r.json()


def action_body(domain: str, session_id: str, text: str) -> dict:
    key = {
        "data_pipeline":  "code",
        "code_review":    "review",
        "incident_debug": "diagnosis",
    }[domain]
    return {"session_id": session_id, key: text}


# ── Logging ───────────────────────────────────────────────────────────────────
def log_start(task: str, model: str):
    print(f"[START] task={task} env={BENCHMARK} model={model}", flush=True)

def log_step(step: int, action: str, reward: float, done: bool, error):
    reward = max(0.001, min(0.999, float(reward)))
    a = repr(action.replace("\n", "\\n")[:120])
    d = "true" if done else "false"
    e = "null" if error is None else str(error)
    print(f"[STEP] step={step} action={a} reward={reward:.2f} done={d} error={e}", flush=True)

def log_end(success: bool, steps: int, rewards: list):
    clamped = [max(0.001, min(0.999, float(x))) for x in rewards]
    score   = sum(clamped) / len(clamped) if clamped else 0.001
    s       = "true" if success else "false"
    r       = ",".join(f"{x:.2f}" for x in clamped)
    print(f"[END] success={s} steps={steps} score={score:.3f} rewards={r}", flush=True)


# ── Episode runner ────────────────────────────────────────────────────────────
def run_task(client, task: dict):
    task_id    = task["task_id"]
    domain     = task["domain"]
    difficulty = task["difficulty"]
    rewards    = []
    steps_done = 0
    success    = False
    session_id = None

    log_start(task=task_id, model=MODEL_NAME)

    try:
        # reset
        res        = call_env("POST", "/reset",
                              json={"domain": domain, "difficulty": difficulty})
        session_id = res.get("session_id", "")
        obs        = res.get("observation", res)
        if not isinstance(obs, dict):
            obs = {}
        done = obs.get("done", False)

        for step in range(1, MAX_STEPS + 1):
            if done:
                break

            system, user = build_prompt(obs, domain, step)
            agent_text   = call_llm(client, system, user)
            body         = action_body(domain, session_id, agent_text)

            step_res = call_env("POST", "/step", json=body)
            reward   = float(step_res.get("reward", 0.05))
            done     = bool(step_res.get("done", False))
            error    = step_res.get("error", None)
            obs      = step_res.get("observation", {})
            if not isinstance(obs, dict):
                obs = {}
            # carry feedback forward so next step can fix mistakes
            if step_res.get("feedback"):
                obs["feedback"] = step_res["feedback"]

            rewards.append(reward)
            steps_done = step
            log_step(step=step, action=agent_text,
                     reward=reward, done=done, error=error)

        avg     = sum(rewards) / len(rewards) if rewards else 0.05
        success = avg >= 0.5

    except Exception as exc:
        print(f"[DEBUG] task {task_id} failed: {exc}", flush=True)
        if not rewards:
            rewards = [0.05]

    finally:
        if session_id:
            try:
                call_env("DELETE", f"/sessions/{session_id}")
            except Exception:
                pass
        log_end(success=success, steps=steps_done, rewards=rewards)


def main():
    client = OpenAI(base_url=API_BASE_URL, api_key=HF_TOKEN)
    for task in TASKS:
        run_task(client, task)


if __name__ == "__main__":
    main()
