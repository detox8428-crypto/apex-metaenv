
---
title: APEX Engineering Benchmark
emoji: 🏗️
colorFrom: purple
colorTo: blue
sdk: docker
app_file: app.py
pinned: false
license: mit
tags:
  - openenv
  - reinforcement-learning
  - engineering
  - real-world
  - rl-benchmark
---

#  APEX Engineering Benchmark

> The RL benchmark where agents learn to think like senior engineers.

[![OpenEnv v1](https://img.shields.io/badge/OpenEnv-v1%20Compliant-brightgreen)](https://openenv.dev)
[![Status](https://img.shields.io/badge/Status-Running-success)](https://huggingface.co/spaces/ShaikB/Apex)
[![Tasks](https://img.shields.io/badge/Tasks-9-orange)](#domains)
[![License](https://img.shields.io/badge/License-MIT-purple)](LICENSE)

**[Live Space](https://huggingface.co/spaces/ShaikB/Apex) · [API Docs](https://shaikb-apex.hf.space/docs) · [Health Check](https://shaikb-apex.hf.space/health)**

---

## What is APEX?

Most RL benchmarks train agents to optimize numbers. APEX trains agents to think like engineers.

Three domains, each requiring different multi-step reasoning:

- **Data Pipeline** — write pandas code that passes hidden test cases
- **Code Review** — identify bugs and explain their production impact
- **Incident Debug** — diagnose a live outage as new logs are revealed each step

---

## Domains

### Data Pipeline

| Task | Function | Difficulty |
|------|----------|------------|
| `dp-easy-001` | `aggregate_sales(df)` — group by customer, sum amounts | Easy |
| `dp-medium-001` | `clean_transactions(df)` — dedup + fillna | Medium |
| `dp-hard-001` | `compare_dates(df)` — normalize mixed tz-aware timestamps | Hard |

### Code Review

| Task | Bug | Difficulty |
|------|-----|------------|
| `cr-easy-001` | N+1 query in Django ORM loop | Easy |
| `cr-medium-001` | Race condition in Redis counter | Medium |
| `cr-hard-001` | Missing WHERE clause on bulk update | Hard |

### Incident Debug

| Task | Incident | Difficulty |
|------|----------|------------|
| `id-easy-001` | Auth service timeout | Easy |
| `id-medium-001` | Connection pool exhaustion → retry storm | Medium |
| `id-hard-001` | Distributed meltdown — circuit breaker stuck open | Hard |

---

## API

Start an episode:

```bash
curl -X POST https://shaikb-apex.hf.space/reset \
  -H "Content-Type: application/json" \
  -d '{"domain": "data_pipeline", "difficulty": "easy"}'
```

Submit an action:

```bash
curl -X POST https://shaikb-apex.hf.space/step \
  -H "Content-Type: application/json" \
  -d '{"session_id": "...", "code": "def aggregate_sales(df): ..."}'
```

All endpoints: `/reset` `/step` `/state/{id}` `/health` `/tasks` `/manifest` `/docs`

---

## Reward Design

Rewards are always in `[0.0, 1.0]`. Never binary — every improvement gets a signal.

- **Data Pipeline:** partial credit per test case passed + efficiency bonus
- **Code Review:** production keyword coverage + fix quality
- **Incident Debug:** keyword match per step, final score = max across steps

---

## Baseline Results

Tested with `Qwen/Qwen2.5-72B-Instruct` via HuggingFace Inference Router.

| Domain | Easy | Medium | Hard | Avg |
|--------|:----:|:------:|:----:|:---:|
| Data Pipeline | 1.00 | 0.95 | 0.95 | **0.97** |
| Code Review | 1.00 | 0.86 | 0.80 | **0.89** |
| Incident Debug | 0.90 | 1.00 | 0.90 | **0.93** |
| **Overall** | **0.97** | **0.94** | **0.88** | **0.93** |

All 9/9 tasks passing. Runtime ~12 minutes on 2 vCPU / 8GB RAM.

```
[START] task=easy-solve-001 env=apex-engineering-benchmark model=Qwen/Qwen2.5-72B-Instruct
[STEP]  step=1 action="def aggregate_sales(df):..." reward=1.00 done=true error=null
[END]   success=true steps=1 rewards=1.00

[START] task=id-medium-001 env=apex-engineering-benchmark model=Qwen/Qwen2.5-72B-Instruct
[STEP]  step=1 action="ROOT CAUSE: connection pool exhausted..." reward=1.00 done=false error=null
[STEP]  step=2 action="ROOT CAUSE: retry storm cascading..." reward=1.00 done=true error=null
[END]   success=true steps=2 rewards=1.00,1.00
```

---

## Run It

```bash
# Clone and install
git clone https://huggingface.co/spaces/ShaikB/Apex
cd Apex
pip install -r requirements.txt
python app.py
```

```bash
# Run baseline inference
export HF_TOKEN=your_token
export API_BASE_URL=https://router.huggingface.co/v1
export MODEL_NAME=Qwen/Qwen2.5-72B-Instruct
export SPACE_URL=https://shaikb-apex.hf.space
python inference.py
```

---

## Project Structure

```
├── app.py           # FastAPI server (OpenEnv v1 endpoints)
├── environment.py   # Session management
├── graders.py       # Reward calculators for each domain
├── tasks.py         # 9 task definitions
├── models.py        # Pydantic models
├── inference.py     # Baseline runner
├── openenv.yaml     # OpenEnv spec
└── Dockerfile
```

---

*Built for the Meta × HuggingFace OpenEnv Bootcamp 2026*
