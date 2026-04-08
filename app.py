"""
APEX Engineering Benchmark - FastAPI Server
Implements OpenEnv v1 specification
Single worker mode for reliable session management
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import os
import logging
from typing import Optional

from models import ResetRequest, ResetResponse, StepRequest, StepResponse
from environment import APEXEnvironment

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
    domain: str = Query(default="data_pipeline"),
    difficulty: str = Query(default="easy"),
    mode: str = Query(default="solve"),
    body: Optional[ResetRequest] = None
):
    """
    Reset environment (OpenEnv spec)
    
    Supports query parameters:
    - POST /reset?domain=data_pipeline&difficulty=easy
    - POST /reset?domain=code_review&difficulty=medium
    
    Also accepts JSON body for flexibility
    """
    try:
        # Accept both query params and JSON body
        d = domain
        diff = difficulty
        if body:
            d = body.domain or domain
            diff = body.difficulty or difficulty
        
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
    logger.info("  POST /reset  - Start new episode")
    logger.info("  POST /step   - Submit action (code/review/diagnosis)")
    logger.info("  GET  /state  - Get session state")
    logger.info("  GET  /health - Health check")
    logger.info("  GET  /docs   - API documentation")
    logger.info("=" * 70)


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 7860))
    uvicorn.run(app, host="0.0.0.0", port=port, workers=1)
