<div align="center">

# 🏗️ APEX Engineering Benchmark

### The RL benchmark where agents learn to debug production, not just score points.

[![OpenEnv v1](https://img.shields.io/badge/OpenEnv-v1%20Compliant-brightgreen?style=flat-square)](https://openenv.dev)
[![Tasks](https://img.shields.io/badge/Tasks-29%20Real%20World-orange?style=flat-square)](#tasks)
[![License](https://img.shields.io/badge/License-MIT-purple?style=flat-square)](LICENSE)

[🚀 Live Demo](https://huggingface.co/spaces/ShaikB/Apex) · [📊 API Docs](https://shaikb-apex.hf.space/docs) · [🏆 Leaderboard](https://shaikb-apex.hf.space/leaderboard)

</div>

---

## Why APEX?

Most RL benchmarks train agents to **score points**. APEX trains agents to **think like engineers.**

| What agents learn | APEX | Typical RL Envs |
|---|:---:|:---:|
| Debug production outages | ✅ | ❌ |
| Review code at scale | ✅ | ❌ |  
| Fix real data pipeline bugs | ✅ | ❌ |
| Optimize inventory numbers | ❌ | ✅ |
| Score points in games | ❌ | ✅ |

**An agent trained on APEX can assist real engineers during production incidents, code reviews, and data pipeline failures.**

---

## The 3 Domains

### 1. **Data Pipeline** (11 tasks)
Write pandas code to fix real ETL bugs. Your solution runs in a sandbox with hidden test cases.

- 🟢 **Easy:** Aggregate sales by customer ID
- 🟡 **Medium:** Merge and deduplicate records  
- 🔴 **Hard:** Fix timezone-aware datetime comparison crash

### 2. **Code Review** (9 tasks)
Find bugs in production code and explain the blast radius. Not just syntax errors — architectural and performance issues.

- 🟢 **Easy:** Spot N+1 query affecting database
- 🟡 **Medium:** Identify unhandled exception in API flow
- 🔴 **Hard:** Find 3 interacting security vulnerabilities in payment service

### 3. **Incident Debug** (9 tasks)
Diagnose cascading failures from logs and metrics, revealed step-by-step. You have 3 turns to identify root cause and fix.

- 🟢 **Easy:** Auth service timeout — single root cause
- 🟡 **Medium:** Memory leak in long-running service
- 🔴 **Hard:** Intermittent 500 errors with no pattern or stack trace

---

## API Endpoints

### Reset: Start a new episode

```bash
curl -X POST "https://shaikb-apex.hf.space/reset?domain=data_pipeline&difficulty=easy"
```

### Step: Submit your action

```bash
curl -X POST "https://shaikb-apex.hf.space/step" \
  -H "Content-Type: application/json" \
  -d '{"session_id": "...", "code": "def solve(df):\n    return df.groupby(\"customer_id\")[\"amount\"].sum()"}'
```

### Get Session: Fetch current state

```bash
curl "https://shaikb-apex.hf.space/state/{session_id}"
```

### Leaderboard: See top scores

```bash  
curl "https://shaikb-apex.hf.space/leaderboard?limit=10"
```

### List Tasks: What's available

```bash
curl "https://shaikb-apex.hf.space/tasks"
```

### Compare Domains: Why APEX differs

```bash
curl "https://shaikb-apex.hf.space/compare"
```

### Delete Session: Cleanup

```bash
curl -X DELETE "https://shaikb-apex.hf.space/sessions/{session_id}"
```

---

## Baseline Performance

**Tested Live Baseline (Qwen 2.5 72B):**

| Domain | Easy | Medium | Hard | Domain Avg |
|---|:---:|:---:|:---:|:---:|
| **Data Pipeline** | 1.00 | 0.95 | 0.00 | **0.65** |
| **Code Review** | 1.00 | 0.86 | 0.72 | **0.86** |
| **Incident Debug** | 0.70 | 0.55* | 0.43* | **0.56** |
| **Avg** | **0.90** | **0.79** | **0.38** | **0.69** |

*Multi-step tasks (final score shown; medium=2 steps, hard=3 steps)

**Evidence:** Scores generated live from [HF Space](https://shaikb-apex.hf.space/docs) endpoints with real graders.py fence-stripping active. Model has 3 attempts per task for iterative debugging (incident_debug) and code generation (data_pipeline).

---

## Deploy & Run

### Local (Docker)

```bash
docker run -p 7860:7860 \
  -e OPENAI_API_KEY=your_key \
  -e API_BASE_URL=http://localhost:7860 \
  ShaikB/Apex
```

### Local (Python)

```bash
pip install -r requirements.txt
export OPENAI_API_KEY=your_key
python app.py
```

---

## Pre-Submission Checklist

- [x] Passes `openenv validate` (entry point: `server = "app:app"`)
- [x] All 9 endpoints respond correctly
- [x] Leaderboard endpoint tracks sessions
- [x] Tasks endpoint returns all 29 tasks
- [x] Domain comparison available
- [x] Health check passes
- [x] API docs accessible at `/docs`
- [x] 29 deterministic tasks across 3 domains
- [x] Grading logic verified

---

## Links

- **GitHub:** https://github.com/RAMANABOYANA-UK/APEX
- **HuggingFace:** https://huggingface.co/spaces/ShaikB/Apex
- **API Docs:** https://shaikb-apex.hf.space/docs
- **Leaderboard:** https://shaikb-apex.hf.space/leaderboard
- **Domain Comparison:** https://shaikb-apex.hf.space/compare

---

## License

MIT
