"""
APEX Engineering Benchmark - FastAPI Server
Implements OpenEnv v1 specification
"""

from fastapi import FastAPI, HTTPException, Query, Body, Request
from fastapi.middleware.cors import CORSMiddleware
import os
import logging
import json
from typing import Optional

from models import ResetRequest, ResetResponse, StepRequest, StepResponse, Observation
from environment import APEXEnvironment

# File-based session storage for multi-worker HF Spaces
SESSION_DIR = "/tmp/apex_sessions"
os.makedirs(SESSION_DIR, exist_ok=True)

def _save_session(session_id: str, data: dict) -> None:
    """Save session data to JSON file"""
    path = os.path.join(SESSION_DIR, f"{session_id}.json")
    with open(path, 'w') as f:
        json.dump(data, f, default=str)

def _load_session(session_id: str) -> Optional[dict]:
    """Load session data from JSON file"""
    path = os.path.join(SESSION_DIR, f"{session_id}.json")
    if not os.path.exists(path):
        return None
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except:
        return None

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
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

# Create global environment instance
env = APEXEnvironment()


# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "ok",
        "version": "3.0.0",
        "active_sessions": len(env.sessions)
    }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "APEX Engineering Benchmark",
        "version": "3.0.0",
        "api_docs": "/docs",
        "endpoints": ["/reset", "/step", "/state", "/health"]
    }


# ============================================================================
# OPENENV SPEC ENDPOINTS
# ============================================================================

@app.post("/reset", response_model=ResetResponse)
async def reset_env(
    domain: str = Query(default="data_pipeline"),
    difficulty: str = Query(default="easy"),
    mode: str = Query(default="solve"),
):
    """
    Reset environment (OpenEnv spec)
    
    Supports query parameters:
    - POST /reset?domain=data_pipeline&difficulty=easy
    - POST /reset?domain=code_review&difficulty=medium
    
    Returns: {session_id, observation}
    """
    try:
        session_id, observation = env.reset(
            domain=domain,
            difficulty=difficulty,
            mode=mode
        )
        
        # Save session to file for multi-worker persistence
        _save_session(session_id, {
            "session_id": session_id,
            "domain": domain,
            "difficulty": difficulty,
            "mode": mode,
            "step": 0,
            "rewards": [],
            "done": False,
            "history": []
        })
        
        logger.info(f"Reset: session={session_id[:8]}... domain={domain} difficulty={difficulty}")
        
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
    Alternative: Reset environment with JSON body (for compatibility)
    
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
        
        # Save session to file for multi-worker persistence
        _save_session(session_id, {
            "session_id": session_id,
            "domain": request.domain,
            "difficulty": request.difficulty,
            "mode": request.mode,
            "step": 0,
            "rewards": [],
            "done": False,
            "history": []
        })
        
        logger.info(f"Reset: session={session_id[:8]}... domain={request.domain} difficulty={request.difficulty}")
        
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
    try:
        # For multi-worker HF Spaces: if session not in env.sessions, try to restore from file
        if request.session_id not in env.sessions:
            session_file = _load_session(request.session_id)
            if not session_file:
                raise HTTPException(status_code=404, detail=f"Session {request.session_id} not found")
            # Session file exists, but we can't fully reconstruct the environment context
            # For now, just confirm it exists
            logger.info(f"Session {request.session_id[:8]}... exists in file storage")
        
        # Run step with environment
        observation, reward, done, info = env.step(
            session_id=request.session_id,
            code=request.code,
            review=request.review,
            diagnosis=request.diagnosis
        )
        
        # Update session file with new step data
        session_data = _load_session(request.session_id)
        if not session_data:
            session_data = {
                "session_id": request.session_id,
                "step": 0,
                "rewards": [],
                "done": False,
                "history": []
            }
        
        session_data["step"] = info.get("step", 0)
        session_data["done"] = done
        if "rewards" not in session_data:
            session_data["rewards"] = []
        session_data["rewards"].append(reward)
        
        if "history" not in session_data:
            session_data["history"] = []
        session_data["history"].append({
            "step": info.get("step", 0),
            "reward": reward,
            "feedback": info.get("feedback", "")
        })
        _save_session(request.session_id, session_data)
        
        logger.info(
            f"Step: session={request.session_id[:8]}... "
            f"step={info.get('step')} reward={reward:.2f} done={done}"
        )
        
        return {
            "session_id": request.session_id,
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
async def get_state(session_id: Optional[str] = Query(default=None)):
    """
    Get session state (OpenEnv spec)
    
    GET /state?session_id={id}
    """
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id parameter required")
    
    try:
        session_data = _load_session(session_id)
        if not session_data:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
        return session_data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"State error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/state/{session_id}")
async def get_state_path(session_id: str):
    """
    Get session state by path parameter (OpenEnv spec)
    
    GET /state/{session_id}
    """
    try:
        session_data = _load_session(session_id)
        if not session_data:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
        return session_data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"State error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# STARTUP LOGGING
# ============================================================================

@app.on_event("startup")
async def startup_event():
    logger.info("=" * 60)
    logger.info("APEX Engineering Benchmark - FastAPI Server")
    logger.info("Version: 3.0.0 (OpenEnv v1 Compliant)")
    logger.info("=" * 60)
    logger.info("Endpoints:")
    logger.info("  POST /reset  - Start new episode")
    logger.info("  POST /step   - Submit action (code/review/diagnosis)")
    logger.info("  GET  /state  - Get session state")
    logger.info("  GET  /health - Health check")
    logger.info("  GET  /docs   - API documentation")
    logger.info("=" * 60)


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 7860))
    uvicorn.run(app, host="0.0.0.0", port=port)
