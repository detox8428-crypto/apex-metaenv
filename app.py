"""
APEX Engineering Benchmark - FastAPI Server
Implements OpenEnv v1 specification
"""

from fastapi import FastAPI, HTTPException, Query, Body, Request
from fastapi.middleware.cors import CORSMiddleware
import os
import logging
from typing import Optional

from models import ResetRequest, ResetResponse, StepRequest, StepResponse, Observation
from environment import APEXEnvironment

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
    body: Optional[ResetRequest] = Body(default=None),
):
    """
    Reset environment (OpenEnv spec)
    
    Supports BOTH:
    - Query params: POST /reset?domain=data_pipeline&difficulty=easy
    - JSON body: POST /reset with {"domain": "data_pipeline", "difficulty": "easy"}
    
    Returns: {session_id, observation}
    """
    try:
        # Use body values only if query params are at their defaults
        # This gives priority to explicitly passed query params
        final_domain = domain
        final_difficulty = difficulty
        final_mode = "solve"
        
        # If body provided and query params are defaults, use body values
        if body and domain == "data_pipeline" and difficulty == "easy":
            final_domain = body.domain
            final_difficulty = body.difficulty
            final_mode = body.mode
        
        session_id, observation = env.reset(
            domain=final_domain,
            difficulty=final_difficulty,
            mode=final_mode
        )
        
        logger.info(f"Reset: session={session_id[:8]}... domain={final_domain} difficulty={final_difficulty}")
        
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
        observation, reward, done, info = env.step(
            session_id=request.session_id,
            code=request.code,
            review=request.review,
            diagnosis=request.diagnosis
        )
        
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
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Step error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/state")
async def get_state(session_id: Optional[str] = Query(default=None)):
    """
    Get session state (OpenEnv spec)
    
    Supports both:
    - Query param: GET /state?session_id={id}
    - Path param: GET /state/{id}
    """
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id parameter required")
    
    try:
        return env.state(session_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"State error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/state/{session_id}")
async def get_state_path(session_id: str):
    """
    Get session state by path parameter (OpenEnv spec)
    """
    try:
        return env.state(session_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
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
