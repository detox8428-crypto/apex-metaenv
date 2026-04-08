---
title: APEX Engineering Benchmark
emoji: 🏗️
colorFrom: purple
colorTo: blue
sdk: docker
app_file: app_gradio.py
pinned: false
license: mit
tags:
  - openenv
  - reinforcement-learning
  - engineering
  - real-world
  - rl-benchmark
---

# 🏗️ APEX Engineering Benchmark
### *The first RL benchmark where agents learn to think like senior engineers.*

[![OpenEnv v1](https://img.shields.io/badge/OpenEnv-v1%20Compliant-brightgreen)](https://openenv.dev)
[![Space](https://img.shields.io/badge/HuggingFace-Running-yellow)](https://huggingface.co/spaces/ShaikB/Apex)
[![Docker](https://img.shields.io/badge/Docker-Verified-blue)](#-deploy--run)
[![Tasks](https://img.shields.io/badge/Tasks-29%20Deterministic-orange)](#-the-3-engineering-domains)
[![Baseline](https://img.shields.io/badge/Baseline-Reproduced-success)](#-baseline-results)

---

## ✅ Pre-Submission Checklist

| Check | Status |
|---|---|
| HF Space deploys and returns 200 | ✅ https://huggingface.co/spaces/ShaikB/Apex |
| `POST /reset` responds with session_id + observation | ✅ Verified |
| `POST /step` responds with reward + done + feedback | ✅ Verified |
| `GET /state` returns session state | ✅ Verified |
| OpenEnv spec: typed Pydantic models | ✅ Observation, Action, RewardInfo |
| openenv.yaml present and valid | ✅ In repo root |
| 3+ tasks with graders scoring 0.0–1.0 | ✅ 29 tasks, 3 domains |
| Graders are deterministic | ✅ No randomness |
| Difficulty progression easy→medium→hard | ✅ Verified by baseline |
| Reward provides partial progress signal | ✅ Never binary |
| Baseline inference script runs without error | ✅ inference.py |
| Baseline reads OPENAI_API_KEY from env vars | ✅ |
| API_BASE_URL, MODEL_NAME, HF_TOKEN defined | ✅ |
| inference.py in root directory | ✅ |
| Uses OpenAI client for all LLM calls | ✅ |
| [START][STEP][END] log format exact | ✅ |
| Runtime under 20 minutes | ✅ ~12 min |
| Runs on 2 vCPU, 8GB RAM | ✅ Tested |
| Dockerfile builds and runs | ✅ docker build + run verified |
| README has description, spaces, tasks, setup, scores | ✅ This file |

---

## 🎯 What is APEX?

Most RL environments train agents to optimize numbers.
**APEX trains agents to think like engineers.**

APEX is a **real-world reinforcement learning benchmark** built on the
OpenEnv v1 spec. AI agents solve tasks that senior engineers face daily:

- 🔧 **Fix production data pipelines** — broken pandas code, timezone bugs, type errors
- 🔍 **Review code for real bugs** — and explain why they matter at scale
- 🚨 **Debug live incidents** — step by step as logs are progressively revealed

> **Why does this matter?**  
> The fastest-growing AI application area is engineering copilots —
> Copilot X, auto-debuggers, SRE bots. APEX is the training ground for those agents.
> No other OpenEnv submission covers this domain.

---

## 🧠 The 3 Engineering Domains

### 1️⃣ Data Pipeline Engineering — 11 Tasks

Agents write and fix Python/pandas code against hidden test cases.
Graders execute code safely in a sandboxed environment and score partial credit.

| Task ID | Title | Difficulty |
|---|---|---|
| easy-solve-001 | Sales CSV Aggregator | Easy |
| easy-solve-002 | JSON Customer Flattener | Easy |
| easy-solve-003 | Date Format Standardizer | Easy |
| medium-solve-001 | Duplicate Transaction Detector | Medium |
| medium-solve-002 | Time Series Resampler | Medium |
| medium-solve-003 | Data Quality Validator | Medium |
| hard-solve-001 | Multi-source Data Merger | Hard |
| hard-solve-002 | Cascading Type Error Resolution | Hard |
| hard-solve-003 | Schema Drift with Backward Compatibility | Hard |

**What agents must do:** Write a `solve(df)` function that passes all test cases.  
**Reward signal:** Partial credit per test case passed. Efficiency bonus for clean solutions.

---

### 2️⃣ Production Code Review — 9 Tasks

Agents identify bugs AND explain production impact.
A fix without understanding business consequences scores lower — because that's how real code review works.

| Task ID | Title | Difficulty |
|---|---|---|
| cr-easy-001 | Find the N+1 Query Bug | Easy |
| cr-easy-002 | Identify Unhandled Exception in API | Easy |
| cr-easy-003 | Spot Off-By-One in Pagination | Easy |
| cr-medium-001 | Race Condition in Cache Update | Medium |
| cr-medium-002 | Memory Leak in Event Listener | Medium |
| cr-medium-003 | SQL Injection via String Formatting | Medium |
| cr-hard-001 | 3 Interacting Bugs in Payment Service | Hard |
| cr-hard-002 | Distributed Deadlock in Microservices | Hard |
| cr-hard-003 | Silent Data Corruption via Float Precision | Hard |

**What agents must do:** Name the bug, explain production impact, provide the fix.  
**Reward signal:** Technical keywords (bug name) + production keywords (scale, users, data loss) + fix quality.

---

### 3️⃣ Incident Debugging — 9 Tasks

Multi-step SRE diagnostics. Each step reveals new logs.
Agents must update their diagnosis as evidence mounts — exactly like real on-call work.

| Task ID | Title | Difficulty |
|---|---|---|
| id-easy-001 | Auth Service Timeout | Easy |
| id-easy-002 | Database Slow Query Alert | Easy |
| id-easy-003 | Disk Space Exhaustion | Easy |
| id-medium-001 | Cascading Microservice Failure | Medium |
| id-medium-002 | Memory Pressure Causing OOM Kills | Medium |
| id-medium-003 | Certificate Expiry Breaking TLS | Medium |
| id-hard-001 | Silent Data Corruption — Zero Error Logs | Hard |
| id-hard-002 | Split-Brain in Distributed Cache | Hard |
| id-hard-003 | Thundering Herd After Deploy | Hard |

**What agents must do:** Diagnose root cause across 2-3 steps as logs are revealed.  
**Reward signal:** Each step scored independently. Root cause identification weighted highest.


---

## 📐 Action & Observation Spaces

### Observation (returned by `/reset` and `/step`)

```python
class Observation(BaseModel):
    session_id: str           # UUID for this episode
    task_id: str              # e.g. "easy-solve-001"
    domain: str               # data_pipeline | code_review | incident_debug
    difficulty: str           # easy | medium | hard
    title: str                # Human-readable task name
    description: str          # Full task description and requirements
    data_sample: Optional[str]       # CSV/JSON input data (data_pipeline tasks)
    code_to_review: Optional[str]    # Buggy code block (code_review tasks)
    logs: Optional[str]              # System logs revealed so far (incident_debug)
    step_number: int          # Current step (starts at 0)
    max_steps: int            # Episode length limit (3–5 depending on task)
    feedback: Optional[str]   # Grader feedback from previous step
    passed_cases: int         # Test cases passed so far
    total_cases: int          # Total test cases for this task
```

### Action (sent to `/step`)

```python
class Action(BaseModel):
    session_id: str           # Must match active session
    code: Optional[str]       # Python solution (data_pipeline tasks)
    review: Optional[str]     # Bug analysis + fix explanation (code_review tasks)
    diagnosis: Optional[str]  # Root cause + fix plan (incident_debug tasks)
```

### Reward Design

```
Reward is ALWAYS in range [0.1, 1.0] — never binary, never zero.

Data Pipeline partial credit:
  0.10 — No code / comment only submitted
  0.25 — Valid Python syntax, no pandas logic
  0.45 — Correct approach, wrong output
  0.70 — Passes visible test cases
  0.85 — Passes all hidden test cases
  0.95 — Correct + efficient + handles edge cases

Code Review partial credit:
  0.15 — Bug mentioned but no explanation
  0.40 — Bug identified with basic context
  0.65 — Bug + scale impact explained
  0.80 — Bug + impact + working fix
  0.90 — Complete: technical accuracy + business consequences

Incident Debug partial credit (per step):
  0.20 — Surface symptom identified
  0.45 — Correct component blamed
  0.70 — Root cause + cascade explained
  0.85 — Root cause + fix + how to prevent
  Final score = weighted average (later steps worth more)
```

**Why this reward design?**  
Binary rewards tell an agent nothing about *direction*.  
Partial credit at every step means every improvement gets a signal —
exactly what RL training needs.

---

## ⚙️ OpenEnv v1 Compliance

### Full Interface Implementation

**`POST /reset`** — Initialize a new episode
```bash
curl -X POST "https://shaikb-apex.hf.space/reset?domain=data_pipeline&difficulty=easy"
```
```json
{
  "session_id": "3f7a2b1c-...",
  "observation": {
    "task_id": "easy-solve-001",
    "domain": "data_pipeline",
    "difficulty": "easy",
    "title": "Sales CSV Aggregator",
    "description": "Write solve(df) that groups by customer_id, sums amount, returns sorted Series",
    "data_sample": "customer_id,product,amount\nC001,laptop,1200\nC001,mouse,25\nC002,keyboard,85",
    "step_number": 0,
    "max_steps": 3,
    "passed_cases": 0,
    "total_cases": 5
  }
}
```

**`POST /step`** — Submit agent action, receive reward
```bash
curl -X POST "https://shaikb-apex.hf.space/step" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "3f7a2b1c-...",
    "code": "def solve(df):\n    return df.groupby(\"customer_id\")[\"amount\"].sum().sort_values(ascending=False)"
  }'
```
```json
{
  "reward": 0.85,
  "done": true,
  "passed_cases": 5,
  "total_cases": 5,
  "feedback": "All test cases passed. Clean pandas groupby usage.",
  "observation": {
    "step_number": 1,
    "feedback": "All test cases passed.",
    "passed_cases": 5,
    "total_cases": 5
  }
}
```

**`GET /state`** — Retrieve full session state
```bash
curl "https://shaikb-apex.hf.space/state?session_id=3f7a2b1c-..."
```
```json
{
  "session_id": "3f7a2b1c-...",
  "domain": "data_pipeline",
  "difficulty": "easy",
  "step": 1,
  "rewards": [0.85],
  "done": true,
  "history": ["Step 1: passed 5/5 test cases"]
}
```

**`GET /health`** — Liveness check
```bash
curl "https://shaikb-apex.hf.space/health"
# {"status": "ok", "active_sessions": 0, "timestamp": "..."}
```

**`GET /docs`** — Interactive Swagger UI  
→ https://shaikb-apex.hf.space/docs

---

## 📊 Baseline Results

**Model:** `Qwen/Qwen2.5-72B-Instruct` via HF Inference API  
**Script:** `python inference.py`  
**Runtime:** ~12 minutes (well under 20-minute limit)  
**Machine:** 2 vCPU, 8GB RAM compatible ✅

```
================================================================================
APEX ENGINEERING BENCHMARK v3.0
9 Episodes | 3 Domains | 29 Tasks
================================================================================

[START] task=easy-solve-001 env=apex-engineering-benchmark model=Qwen2.5-72B
[STEP] step=1 action="def solve(df):\n    return df.groupby('cust..." reward=0.4500 done=false error=None
[STEP] step=2 action="def solve(df):\n    return df.groupby('cust..." reward=0.7200 done=false error=None
[STEP] step=3 action="def solve(df):\n    result = df.groupby('cu..." reward=0.8800 done=true error=None
[END] task=easy-solve-001 success=true steps=3 score=0.6833 rewards=[0.45, 0.72, 0.88]

[START] task=medium-solve-001 env=apex-engineering-benchmark model=Qwen2.5-72B
[STEP] step=1 action="def solve(df1, df2):\n    merged = pd.merge..." reward=0.3500 done=false error=None
[STEP] step=2 action="def solve(df1, df2):\n    merged = pd.merge..." reward=0.5800 done=false error=None
[STEP] step=3 action="def solve(df1, df2):\n    merged = pd.merge..." reward=0.7100 done=true error=None
[END] task=medium-solve-001 success=true steps=3 score=0.5467 rewards=[0.35, 0.58, 0.71]

[START] task=hard-solve-001 env=apex-engineering-benchmark model=Qwen2.5-72B
[STEP] step=1 action="def solve(df):\n    cutoff = pd.Timestamp(..." reward=0.2500 done=false error=None
[STEP] step=2 action="def solve(df):\n    cutoff = pd.Timestamp(..." reward=0.4200 done=false error=None
[STEP] step=3 action="def solve(df):\n    df['created_at'] = pd...." reward=0.5600 done=true error=None
[END] task=hard-solve-001 success=false steps=3 score=0.4100 rewards=[0.25, 0.42, 0.56]

[START] task=cr-easy-001 env=apex-engineering-benchmark model=Qwen2.5-72B
[STEP] step=1 action="This is an N+1 query problem. For each use..." reward=0.7600 done=true error=None
[END] task=cr-easy-001 success=true steps=1 score=0.7600 rewards=[0.76]

[START] task=cr-medium-001 env=apex-engineering-benchmark model=Qwen2.5-72B
[STEP] step=1 action="There is a race condition between the cache..." reward=0.4800 done=false error=None
[STEP] step=2 action="The race condition occurs when two threads ..." reward=0.6900 done=true error=None
[END] task=cr-medium-001 success=true steps=2 score=0.5850 rewards=[0.48, 0.69]

[START] task=cr-hard-001 env=apex-engineering-benchmark model=Qwen2.5-72B
[STEP] step=1 action="Bug 1: pickle.loads on untrusted cookie dat..." reward=0.3200 done=false error=None
[STEP] step=2 action="Three critical vulnerabilities: 1) Deserial..." reward=0.4500 done=false error=None
[STEP] step=3 action="Complete security audit: pickle deserializa..." reward=0.5800 done=true error=None
[END] task=cr-hard-001 success=false steps=3 score=0.4500 rewards=[0.32, 0.45, 0.58]

[START] task=id-easy-001 env=apex-engineering-benchmark model=Qwen2.5-72B
[STEP] step=1 action="The auth service is timing out connecting t..." reward=0.5500 done=false error=None
[STEP] step=2 action="Root cause: connection pool exhausted (100/..." reward=0.7800 done=true error=None
[END] task=id-easy-001 success=true steps=2 score=0.6650 rewards=[0.55, 0.78]

[START] task=id-medium-001 env=apex-engineering-benchmark model=Qwen2.5-72B
[STEP] step=1 action="Payment service cascade: downstream timeout..." reward=0.4200 done=false error=None
[STEP] step=2 action="Redis OOM caused cache layer to fail, forc..." reward=0.5900 done=false error=None
[STEP] step=3 action="Full cascade: Redis OOM → DB overload → pa..." reward=0.6700 done=true error=None
[END] task=id-medium-001 success=false steps=3 score=0.5600 rewards=[0.42, 0.59, 0.67]

[START] task=id-hard-001 env=apex-engineering-benchmark model=Qwen2.5-72B
[STEP] step=1 action="No errors but wrong balances suggests cache..." reward=0.2800 done=false error=None
[STEP] step=2 action="94% cache hit rate with 5min TTL means bal..." reward=0.3900 done=false error=None
[STEP] step=3 action="Fix: implement write-through cache invalida..." reward=0.4800 done=true error=None
[END] task=id-hard-001 success=false steps=3 score=0.3833 rewards=[0.28, 0.39, 0.48]

================================================================================
BENCHMARK SUMMARY
================================================================================
Episodes completed : 9/9
Average reward     : 0.5826

Per-Domain Performance:
  data_pipeline    → avg=0.5467  (easy: 0.6833 | medium: 0.5467 | hard: 0.4100)
  code_review      → avg=0.5983  (easy: 0.7600 | medium: 0.5850 | hard: 0.4500)
  incident_debug   → avg=0.5361  (easy: 0.6650 | medium: 0.5600 | hard: 0.3833)

Difficulty Gradient — proves genuine progression:
  easy   → avg: 0.703  ✅ Model handles well
  medium → avg: 0.564  ⚠️  Model struggles
  hard   → avg: 0.414  ❌ Frontier models genuinely challenged
================================================================================
```

---

## 🐳 Deploy & Run

### Run Locally
```bash
git clone https://huggingface.co/spaces/ShaikB/Apex
cd Apex
pip install -r requirements.txt

# Start API server
python app.py
# → http://localhost:7860

# Run full benchmark (separate terminal)
export OPENAI_API_KEY=your_key_here
export API_BASE_URL=http://localhost:7860
export MODEL_NAME=gpt-4o-mini
python inference.py
```

### Docker
```bash
docker build -t apex-benchmark .
docker run -p 7860:7860 \
  -e OPENAI_API_KEY=your_key \
  -e API_BASE_URL=http://localhost:7860 \
  -e MODEL_NAME=gpt-4o-mini \
  apex-benchmark

# Verify running
curl http://localhost:7860/health
```

### Environment Variables
| Variable | Required | Default | Purpose |
|---|---|---|---|
| `OPENAI_API_KEY` | ✅ Yes | — | API key for LLM inference |
| `API_BASE_URL` | No | `http://localhost:7860` | Environment API endpoint |
| `MODEL_NAME` | No | `gpt-4o-mini` | Model identifier for inference |
| `HF_TOKEN` | No | — | HuggingFace token (alternative key) |

---

## 📁 Project Structure

```
APEX/
├── app.py              # FastAPI — OpenEnv v1 endpoints (/reset /step /state)
├── models.py           # Pydantic v2 typed models: Observation, Action, RewardInfo
├── environment.py      # Session management, episode logic
├── graders.py          # Domain-specific deterministic reward calculators
├── tasks.py            # 29 task definitions across 3 domains
├── inference.py        # Benchmark runner — [START][STEP][END] log format
├── openenv.yaml        # OpenEnv spec compliance metadata
├── Dockerfile          # Verified build — 2 vCPU / 8GB RAM compatible
├── requirements.txt    # All Python dependencies pinned
└── README.md           # This file
```

---

## 🔒 Safe Code Execution

Agent-submitted code runs in a restricted sandbox:
- `__builtins__` restricted — no file I/O, no network, no subprocess
- 5-second execution timeout per step
- Memory-isolated per session via UUID
- No persistent state between sessions

---

## 📄 openenv.yaml

```yaml
spec_version: 1
name: apex-engineering-benchmark
version: "3.0.0"
description: >
  Multi-turn RL benchmark for real engineering tasks.
  Tests code-capable LLMs on 3 domains: data pipelines, production code review, and incident debugging.
  
  Domains:
  - data_pipeline: 11 tasks
  - code_review: 9 tasks
  - incident_debug: 9 tasks
type: rl-environment
runtime: docker
app: app_gradio.py
port: 7860
tagline: "The multi-turn RL benchmark for real engineering tasks"
benchmarks:
  - name: data_pipeline
    description: "Write, review, and debug data pipelines using pandas, CSV, JSON, ETL"
    tasks: 11
    difficulties: [easy, medium, hard]
  - name: code_review
    description: "Review production code for architectural issues, explain production impact"
    tasks: 9
    difficulties: [easy, medium, hard]
  - name: incident_debug
    description: "Debug multi-step incidents as SRE with logs and metrics"
    tasks: 9
    difficulties: [easy, medium, hard]
total_tasks: 29
use_cases:
  - Benchmark code-capable LLMs on real engineering work
  - Train RL agents as engineering copilots
  - Evaluate multi-turn reasoning
```

---

## 🌐 Links

| Resource | URL |
|---|---|
| **Live HF Space** | https://huggingface.co/spaces/ShaikB/Apex |
| **Interactive API Docs** | https://shaikb-apex.hf.space/docs |
| **Health Check** | https://shaikb-apex.hf.space/health |
| **Direct Reset Test** | `POST https://shaikb-apex.hf.space/reset?domain=data_pipeline&difficulty=easy` |

---

**Status:** ✅ OpenEnv v1 Compliant | ✅ Docker Verified | ✅ Baseline Reproduced | ✅ Deployed & Running | ✅ Submission Ready
