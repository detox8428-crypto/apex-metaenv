"""
APEX Engineering Benchmark - FastAPI Server
Implements OpenEnv v1 specification
Single worker mode for reliable session management
"""

from fastapi import FastAPI, HTTPException, Query, Body
from fastapi.middleware.cors import CORSMiddleware
import os
import logging
from typing import Optional

from models import ResetRequest, ResetResponse, StepRequest, StepResponse
from environment import APEXEnvironment
from tasks import get_task_by_id

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# MODULE-LEVEL SESSION STORAGE (Single worker = always same process)
# ============================================================================

SESSIONS = {}  # Global dict - reliable with --workers 1

# ============================================================================
# FASTAPI APP SETUP
# ============================================================================

app = FastAPI(
    title="APEX Engineering Benchmark",
    description="Real-world RL environment for data pipelines, code review, and incident debugging",
    version="3.0.0",
    docs_url="/docs"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create environment
env = APEXEnvironment()


# ============================================================================
# ENDPOINTS
# ============================================================================

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "APEX Engineering Benchmark",
        "version": "3.0.0",
        "spec": "openenv/v1",
        "status": "running",
        "endpoints": {
            "reset": "POST /reset",
            "step": "POST /step",
            "state": "GET /state",
            "health": "GET /health",
            "docs": "GET /docs"
        },
        "domains": ["data_pipeline", "code_review", "incident_debug"],
        "tasks": 29
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "ok",
        "version": "3.0.0",
        "workers": 1,
        "active_sessions": len(SESSIONS)
    }


@app.post("/reset", response_model=ResetResponse)
async def reset_env(
    domain: str = Query(default=None),
    difficulty: str = Query(default=None),
    mode: str = Query(default="solve"),
    body: Optional[ResetRequest] = Body(None)
):
    """
    Reset environment (OpenEnv spec)
    
    Supports multiple request formats:
    1. Query params: POST /reset?domain=data_pipeline&difficulty=easy
    2. JSON body with task_id: POST /reset with {"task": "easy-solve-001"}
    3. JSON body with domain/difficulty: POST /reset with {"domain": "data_pipeline", "difficulty": "easy"}
    """
    try:
        d = domain
        diff = difficulty
        
        # Handle body parameters
        if body:
            # If task_id is provided, look it up
            if body.task:
                domain_val, difficulty_val, task = get_task_by_id(body.task)
                if domain_val is None:
                    raise HTTPException(status_code=404, detail=f"Task '{body.task}' not found")
                d = domain_val
                diff = difficulty_val
            else:
                # Otherwise use domain/difficulty from body
                d = body.domain or d or "data_pipeline"
                diff = body.difficulty or diff or "easy"
                mode = body.mode or mode
        else:
            # Use query parameters with defaults
            d = d or "data_pipeline"
            diff = diff or "easy"
        
        # Reset environment
        session_id, observation = env.reset(domain=d, difficulty=diff, mode=mode)
        
        # SAVE TO GLOBAL SESSIONS DICT (single worker = always same process)
        SESSIONS[session_id] = {
            "session_id": session_id,
            "domain": d,
            "difficulty": diff,
            "step": 0,
            "rewards": [],
            "done": False,
            "observation": observation if isinstance(observation, dict) else (observation.dict() if hasattr(observation, 'dict') else str(observation))
        }
        
        logger.info(f"Reset: session={session_id[:8]}... domain={d} difficulty={diff} total_sessions={len(SESSIONS)}")
        
        return {
            "session_id": session_id,
            "observation": observation
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Reset error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/reset/json", response_model=ResetResponse)
async def reset_env_json(request: ResetRequest):
    """
    Alternative: Reset with JSON body
    
    POST /reset/json
    {
        "domain": "data_pipeline",
        "difficulty": "easy",
        "mode": "solve"
    }
    """
    try:
        session_id, observation = env.reset(
            domain=request.domain,
            difficulty=request.difficulty,
            mode=request.mode
        )
        
        # SAVE TO GLOBAL SESSIONS DICT
        SESSIONS[session_id] = {
            "session_id": session_id,
            "domain": request.domain,
            "difficulty": request.difficulty,
            "step": 0,
            "rewards": [],
            "done": False,
            "observation": observation if isinstance(observation, dict) else (observation.dict() if hasattr(observation, 'dict') else str(observation))
        }
        
        logger.info(f"Reset/json: session={session_id[:8]}... domain={request.domain} difficulty={request.difficulty}")
        
        return {
            "session_id": session_id,
            "observation": observation
        }
    except Exception as e:
        logger.error(f"Reset error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/step", response_model=StepResponse)
async def step_env(request: StepRequest):
    """
    Step environment (OpenEnv spec)
    
    Submit: {session_id, code/review/diagnosis}
    Returns: {observation, reward, done, feedback, info}
    """
    session_id = request.session_id
    
    # CHECK GLOBAL SESSIONS DICT
    if session_id not in SESSIONS:
        available = list(SESSIONS.keys())[:3]
        logger.error(f"Session not found: {session_id[:8]}... Available: {available}")
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    
    try:
        # Run step
        observation, reward, done, info = env.step(
            session_id=session_id,
            code=request.code,
            review=request.review,
            diagnosis=request.diagnosis
        )
        
        # UPDATE GLOBAL SESSIONS DICT
        SESSIONS[session_id]["step"] = info.get("step", 0)
        SESSIONS[session_id]["done"] = done
        SESSIONS[session_id]["rewards"].append(reward)
        
        logger.info(
            f"Step: session={session_id[:8]}... "
            f"step={info.get('step')} reward={reward:.2f} done={done}"
        )
        
        return {
            "session_id": session_id,
            "observation": observation,
            "reward": reward,
            "done": done,
            "passed_cases": info.get("passed_cases"),
            "total_cases": info.get("total_cases"),
            "feedback": info.get("feedback", ""),
            "info": info
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Step error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/state")
async def get_state(session_id: str = Query(...)):
    """
    Get session state (OpenEnv spec)
    
    GET /state?session_id={id}
    """
    # LOAD FROM GLOBAL SESSIONS DICT
    if session_id not in SESSIONS:
        available = list(SESSIONS.keys())[:3]
        logger.error(f"State 404: {session_id[:8]}... not found. Available: {available} (total={len(SESSIONS)})")
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    
    try:
        return SESSIONS[session_id]
    except Exception as e:
        logger.error(f"State error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/state/{session_id}")
async def get_state_path(session_id: str):
    """
    Get session state by path parameter (OpenEnv spec)
    
    GET /state/{session_id}
    """
    # LOAD FROM GLOBAL SESSIONS DICT
    if session_id not in SESSIONS:
        available = list(SESSIONS.keys())[:3]
        logger.error(f"State 404: {session_id[:8]}... not found. Available: {available} (total={len(SESSIONS)})")
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    
    try:
        return SESSIONS[session_id]
    except Exception as e:
        logger.error(f"State error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/leaderboard")
async def leaderboard(limit: int = Query(10, ge=1, le=100)):
    """
    Get top sessions by reward with domain stats (leaderboard)
    
    GET /leaderboard?limit=10
    """
    try:
        all_sessions = list(SESSIONS.values())
        completed = [s for s in all_sessions if s.get("rewards")]
        ranked = sorted(completed, key=lambda x: max(x["rewards"]), reverse=True)[:limit]
        
        # Domain breakdown stats
        domain_stats = {}
        for s in all_sessions:
            d = s.get("domain", "unknown")
            if d not in domain_stats:
                domain_stats[d] = {"sessions": 0, "avg_reward": 0, "best_reward": 0}
            domain_stats[d]["sessions"] += 1
            if s.get("rewards"):
                best = max(s["rewards"])
                domain_stats[d]["best_reward"] = max(domain_stats[d]["best_reward"], best)
                domain_stats[d]["avg_reward"] = round(
                    (domain_stats[d]["avg_reward"] + best) / 2, 4
                )
        
        return {
            "total_sessions": len(all_sessions),
            "completed_sessions": len(completed),
            "domain_stats": domain_stats,
            "leaderboard": [
                {
                    "rank": i + 1,
                    "session_id": s["session_id"],
                    "domain": s.get("domain", "unknown"),
                    "difficulty": s.get("difficulty", "unknown"),
                    "best_reward": round(max(s["rewards"]), 4),
                    "steps": s.get("step", 0),
                    "rewards": [round(r, 4) for r in s.get("rewards", [])]
                }
                for i, s in enumerate(ranked)
            ]
        }
    except Exception as e:
        logger.error(f"Leaderboard error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/tasks")
async def list_tasks():
    """
    List all available tasks (OpenEnv extension)
    
    GET /tasks
    """
    return {
        "total_tasks": 9,
        "domains": {
            "data_pipeline": {
                "description": "Fix broken data pipelines in production",
                "difficulties": ["easy", "medium", "hard"],
                "tasks": 3
            },
            "code_review": {
                "description": "Review code at scale and identify bugs",
                "difficulties": ["easy", "medium", "hard"],
                "tasks": 3
            },
            "incident_debug": {
                "description": "Diagnose and fix production incidents",
                "difficulties": ["easy", "medium", "hard"],
                "tasks": 3
            }
        },
        "reset_endpoint": "POST /reset?domain={domain}&difficulty={difficulty}&mode=solve",
        "modes": ["solve", "diagnose"]
    }


@app.get("/compare")
async def compare_domains():
    """
    Shows difficulty progression across all 3 domains.
    Proves APEX has genuine difficulty scaling, not toy problems.
    
    GET /compare
    """
    return {
        "benchmark": "APEX Engineering Benchmark",
        "insight": "Real engineering tasks show harder difficulty progression than toy benchmarks",
        "domains": {
            "data_pipeline": {
                "description": "Write pandas code to fix real ETL bugs",
                "tasks": 11,
                "easy_example": "Aggregate sales by customer ID",
                "hard_example": "Fix timezone-aware date comparison crash in production",
                "why_hard": "Edge cases in real data cause silent failures"
            },
            "code_review": {
                "description": "Find bugs and explain production impact at scale",
                "tasks": 9,
                "easy_example": "Spot N+1 query affecting database",
                "hard_example": "Find 3 interacting security vulnerabilities in payment service",
                "why_hard": "Requires understanding blast radius, not just syntax"
            },
            "incident_debug": {
                "description": "Diagnose cascading failures as logs are revealed step by step",
                "tasks": 9,
                "easy_example": "Auth service timeout - single root cause",
                "hard_example": "Silent data corruption with zero error logs",
                "why_hard": "No errors to follow - requires inferring from behavior"
            }
        },
        "vs_toy_benchmarks": {
            "APEX": "Agent output is directly useful in real engineering workflows",
            "warehouse_envs": "Agent learns to optimize inventory numbers",
            "leetcode_envs": "Agent learns to pass interview puzzles",
            "game_envs": "Agent learns to score points"
        }
    }


@app.get("/manifest")
async def manifest():
    """
    Get environment manifest (OpenEnv spec)
    
    GET /manifest
    """
    return {
        "name": "apex-engineering-benchmark",
        "version": "3.0.0",
        "spec": "openenv/v1",
        "title": "APEX Engineering Benchmark",
        "description": "RL environment for training agents to think like senior engineers",
        "total_tasks": 9,
        "domains": ["data_pipeline", "code_review", "incident_debug"],
        "difficulty_levels": ["easy", "medium", "hard"],
        "action_space": "Text (code/reviews/diagnoses)",
        "observation_space": "Dict with task_id, domain, difficulty, prompt, context",
        "reward_range": [0.01, 0.99],
        "api_endpoints": {
            "reset": {"method": "POST", "path": "/reset", "description": "Start new episode"},
            "step": {"method": "POST", "path": "/step", "description": "Submit action"},
            "state": {"method": "GET", "path": "/state/{session_id}", "description": "Get session state"},
            "compare": {"method": "GET", "path": "/compare", "description": "Domain comparison"},
            "health": {"method": "GET", "path": "/health", "description": "Health check"},
            "leaderboard": {"method": "GET", "path": "/leaderboard", "description": "Get top sessions"},
            "tasks": {"method": "GET", "path": "/tasks", "description": "List available tasks"},
            "manifest": {"method": "GET", "path": "/manifest", "description": "Environment manifest"},
            "delete_session": {"method": "DELETE", "path": "/sessions/{session_id}", "description": "Delete session"}
        },
        "docs_url": "/docs"
    }


@app.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """
    Delete a session (cleanup)
    
    DELETE /sessions/{session_id}
    """
    try:
        if session_id not in SESSIONS:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
        
        del SESSIONS[session_id]
        logger.info(f"Deleted session: {session_id[:8]}...")
        
        return {
            "deleted": session_id,
            "remaining_sessions": len(SESSIONS)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete session error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# STARTUP
# ============================================================================

@app.on_event("startup")
async def startup_event():
    logger.info("=" * 70)
    logger.info("APEX Engineering Benchmark - FastAPI Server")
    logger.info("Version: 3.0.0 (OpenEnv v1 Compliant)")
    logger.info("Mode: Single Worker (--workers 1)")
    logger.info("=" * 70)
    logger.info("Endpoints:")
    logger.info("  POST   /reset              - Start new episode")
    logger.info("  POST   /step               - Submit action (code/review/diagnosis)")
    logger.info("  GET    /state/{session_id} - Get session state")
    logger.info("  GET    /leaderboard        - Top sessions by reward")
    logger.info("  GET    /tasks              - List available tasks")
    logger.info("  GET    /manifest           - Environment manifest")
    logger.info("  DELETE /sessions/{id}      - Delete session")
    logger.info("  GET    /health             - Health check")
    logger.info("  GET    /docs               - API documentation")
    logger.info("=" * 70)



# ============================================================================
# ENTRY POINT FOR SCRIPT
# ============================================================================

def main():
    """Entry point for running the server as a callable from entry points."""
    import uvicorn
    port = int(os.environ.get("PORT", 7860))
    uvicorn.run("app:app", host="0.0.0.0", port=port, workers=1)


# ── Optional Gradio UI mounted at /ui ────────────────────────────────────────
import os
if os.getenv("ENABLE_GRADIO_UI", "true").lower() == "true":
    try:
        import gradio as gr

        with gr.Blocks(title="APEX Engineering Benchmark") as _demo:
            gr.Markdown("""
            # 🏗️ APEX Engineering Benchmark
            **Real-world RL environment** — data pipelines · code review · incident debugging
            
            Use the REST API below or interact manually here.
            """)
            with gr.Row():
                domain_dd = gr.Dropdown(
                    ["data_pipeline", "code_review", "incident_debug"],
                    value="data_pipeline", label="Domain"
                )
                diff_dd = gr.Dropdown(
                    ["easy", "medium", "hard"],
                    value="easy", label="Difficulty"
                )
                reset_btn = gr.Button("Load Task")
            obs_display = gr.Markdown("Click **Load Task** to begin.")
            
            code_input = gr.Textbox(
                lines=12, label="Your solution (code / review / diagnosis)",
                placeholder="Write your solution here..."
            )
            submit_btn = gr.Button("Submit")
            result_display = gr.Markdown("")

            _session = {"id": None, "domain": "data_pipeline"}

            def _reset(domain, difficulty):
                import requests
                r = requests.post(
                    "http://localhost:7860/reset",
                    json={"domain": domain, "difficulty": difficulty}
                ).json()
                _session["id"] = r.get("session_id")
                _session["domain"] = domain
                obs = r.get("observation", {})
                return (
                    f"**Task:** {obs.get('title','')}\n\n"
                    f"**Description:** {obs.get('description','')}\n\n"
                    f"**Step:** {obs.get('step_number',0)}/{obs.get('max_steps',3)}"
                )

            def _step(code):
                if not _session["id"]:
                    return "Load a task first."
                import requests
                domain = _session["domain"]
                key = "code" if domain == "data_pipeline" else ("review" if domain == "code_review" else "diagnosis")
                r = requests.post(
                    "http://localhost:7860/step",
                    json={"session_id": _session["id"], key: code}
                ).json()
                reward = r.get("reward", 0)
                done   = r.get("done", False)
                fb     = r.get("feedback", "")
                return f"**Reward:** {reward:.3f}  |  **Done:** {done}\n\n**Feedback:** {fb}"

            reset_btn.click(_reset, [domain_dd, diff_dd], obs_display)
            submit_btn.click(_step, code_input, result_display)

        app = gr.mount_gradio_app(app, _demo, path="/ui")
        print("✅ Gradio UI mounted at /ui", flush=True)
    except ImportError:
        print("ℹ️  Gradio not installed — UI disabled", flush=True)


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 7860))
    uvicorn.run(app, host="0.0.0.0", port=port, workers=1)
