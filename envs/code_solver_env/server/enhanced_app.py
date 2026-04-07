"""
Enhanced FastAPI Server for APEX - Production Reliability
All endpoints hardened with input validation, error handling, and logging
Maintains full OpenEnv v1 spec compliance
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
import json
import time
import psutil
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from uuid import uuid4
from threading import Lock

from fastapi import FastAPI, HTTPException, Query, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError

from enhanced_models import (
    ResetRequestV2, StepRequestV2, HealthCheckResponseV2, ErrorResponseV2,
    PipelineObservationV2, ResetResponseV2, StepResponseV2, SessionStateV2,
    generate_request_id
)
from .code_solver_environment import CodeSolverEnvironment
from .problems import get_random_problem_by_domain

# ============================================================================
# LOGGING SETUP
# ============================================================================

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# ============================================================================
# GLOBAL STATE & THREAD SAFETY
# ============================================================================

env = CodeSolverEnvironment()
session_lock = Lock()  # Protect concurrent session access
request_metrics = {
    "total_requests": 0,
    "total_errors": 0,
    "errors_last_minute": [],
    "requests_last_minute": []
}
metrics_lock = Lock()
startup_time = time.time()

# ============================================================================
# CONFIGURATION
# ============================================================================

MAX_CONCURRENT_SESSIONS = 500
SESSION_TIMEOUT_SECONDS = 3600  # 1 hour
MAX_REQUEST_SIZE_MB = 10
API_VERSION = "3.0.0"
OPENENV_SPEC = "openenv/v1"

# ============================================================================
# FASTAPI APP
# ============================================================================

app = FastAPI(
    title="APEX Engineering Benchmark v3",
    description="Production-grade RL environment: data pipelines, code review, incident debugging",
    version=API_VERSION,
    docs_url="/docs",
    openapi_url="/openapi.json"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# SESSION MANAGEMENT
# ============================================================================

class SessionManager:
    """Thread-safe session storage with TTL"""
    
    def __init__(self):
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.created_at: Dict[str, datetime] = {}
        self.last_accessed: Dict[str, datetime] = {}
    
    def create_session(self, session_id: str, domain: str, task_type: str, task: Dict) -> bool:
        """Create new session. Returns False if already exists or limit reached."""
        with session_lock:
            # Check session limit
            if len(self.sessions) >= MAX_CONCURRENT_SESSIONS:
                logger.warning(f"Session limit ({MAX_CONCURRENT_SESSIONS}) reached")
                return False
            
            # Check if already exists
            if session_id in self.sessions:
                logger.warning(f"Session {session_id} already exists")
                return False
            
            now = datetime.utcnow()
            self.sessions[session_id] = {
                "domain": domain,
                "task_type": task_type,
                "task": task,
                "step_count": 0,
                "cumulative_reward": 0.0,
                "is_terminal": False,
            }
            self.created_at[session_id] = now
            self.last_accessed[session_id] = now
            
            logger.info(f"Session created: {session_id} ({domain}/{task_type})")
            return True
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session, update last access time. Returns None if not found or expired."""
        with session_lock:
            if session_id not in self.sessions:
                logger.warning(f"Session not found: {session_id}")
                return None
            
            # Check expiry
            if datetime.utcnow() - self.created_at[session_id] > timedelta(seconds=SESSION_TIMEOUT_SECONDS):
                logger.warning(f"Session expired: {session_id}")
                del self.sessions[session_id]
                del self.created_at[session_id]
                del self.last_accessed[session_id]
                return None
            
            # Update last access
            self.last_accessed[session_id] = datetime.utcnow()
            return self.sessions[session_id]
    
    def update_session(self, session_id: str, updates: Dict[str, Any]) -> bool:
        """Update session state. Returns False if not found."""
        with session_lock:
            if session_id not in self.sessions:
                return False
            self.sessions[session_id].update(updates)
            self.last_accessed[session_id] = datetime.utcnow()
            return True
    
    def delete_session(self, session_id: str) -> bool:
        """Delete session. Returns False if not found."""
        with session_lock:
            if session_id not in self.sessions:
                return False
            del self.sessions[session_id]
            del self.created_at[session_id]
            del self.last_accessed[session_id]
            logger.info(f"Session deleted: {session_id}")
            return True
    
    def get_active_count(self) -> int:
        """Get count of active sessions"""
        with session_lock:
            return len(self.sessions)
    
    def cleanup_expired(self) -> int:
        """Remove expired sessions. Returns count removed."""
        with session_lock:
            expired = [
                sid for sid, created in self.created_at.items()
                if datetime.utcnow() - created > timedelta(seconds=SESSION_TIMEOUT_SECONDS)
            ]
            for sid in expired:
                del self.sessions[sid]
                del self.created_at[sid]
                del self.last_accessed[sid]
            if expired:
                logger.info(f"Cleaned up {len(expired)} expired sessions")
            return len(expired)


session_manager = SessionManager()

# ============================================================================
# METRICS TRACKING
# ============================================================================

def track_request(request_id: str, is_error: bool = False):
    """Track request for metrics"""
    with metrics_lock:
        now = datetime.utcnow()
        request_metrics["total_requests"] += 1
        request_metrics["requests_last_minute"].append(now)
        
        if is_error:
            request_metrics["total_errors"] += 1
            request_metrics["errors_last_minute"].append(now)
        
        # Clean old entries (>60 seconds)
        cutoff = now - timedelta(seconds=60)
        request_metrics["requests_last_minute"] = [
            r for r in request_metrics["requests_last_minute"] if r > cutoff
        ]
        request_metrics["errors_last_minute"] = [
            e for e in request_metrics["errors_last_minute"] if e > cutoff
        ]


def get_metrics() -> Dict[str, int]:
    """Get current metrics"""
    with metrics_lock:
        return {
            "total_requests": request_metrics["total_requests"],
            "total_errors": request_metrics["total_errors"],
            "errors_last_minute": len(request_metrics["errors_last_minute"]),
            "requests_last_minute": len(request_metrics["requests_last_minute"]),
        }


# ============================================================================
# ERROR HANDLING
# ============================================================================

def create_error_response(
    error: str,
    error_code: str,
    request_id: str,
    status_code: int = 400,
    details: Optional[str] = None
) -> tuple[Dict[str, Any], int]:
    """Create standardized error response"""
    response = ErrorResponseV2(
        error=error,
        error_code=error_code,
        details=details,
        request_id=request_id
    )
    return response.model_dump(), status_code


@app.exception_handler(ValidationError)
async def validation_exception_handler(request, exc):
    """Handle Pydantic validation errors"""
    request_id = generate_request_id()
    track_request(request_id, is_error=True)
    
    error_details = str(exc).split('\n')[0]  # First line only
    logger.warning(f"Validation error ({request_id}): {error_details}")
    
    body, status = create_error_response(
        error="Invalid request body",
        error_code="VALIDATION_ERROR",
        request_id=request_id,
        status_code=422,
        details=error_details
    )
    return JSONResponse(body, status_code=status)


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions"""
    request_id = generate_request_id()
    track_request(request_id, is_error=True)
    
    logger.warning(f"HTTP error ({request_id}): {exc.status_code} - {exc.detail}")
    
    error_code_map = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        422: "UNPROCESSABLE_ENTITY",
        500: "INTERNAL_SERVER_ERROR",
    }
    
    body, _ = create_error_response(
        error=str(exc.detail),
        error_code=error_code_map.get(exc.status_code, "ERROR"),
        request_id=request_id,
        status_code=exc.status_code,
    )
    return JSONResponse(body, status_code=exc.status_code)


@app.exception_handler(Exception)
async def generic_exception_handler(request, exc):
    """Handle unexpected exceptions - NEVER let them crash"""
    request_id = generate_request_id()
    track_request(request_id, is_error=True)
    
    logger.error(f"Unexpected error ({request_id}): {type(exc).__name__}: {exc}", exc_info=True)
    
    body, status = create_error_response(
        error="Internal server error",
        error_code="INTERNAL_ERROR",
        request_id=request_id,
        status_code=500,
        details="Check server logs with request_id"
    )
    return JSONResponse(body, status_code=status)


# ============================================================================
# ENDPOINTS - HEALTH & INFO
# ============================================================================

@app.get("/health", response_model=HealthCheckResponseV2)
async def health_check():
    """
    Health check endpoint - responds in <100ms
    Returns: status, active sessions, uptime, memory usage
    """
    try:
        request_id = generate_request_id()
        track_request(request_id)
        
        # Cleanup expired sessions
        session_manager.cleanup_expired()
        
        process = psutil.Process()
        memory_mb = process.memory_info().rss / 1024 / 1024
        uptime = time.time() - startup_time
        
        metrics = get_metrics()
        
        status_value = "ok"
        if metrics["errors_last_minute"] > 5:
            status_value = "degraded"
        if memory_mb > 500:
            status_value = "degraded"
        
        return HealthCheckResponseV2(
            status=status_value,
            active_sessions=session_manager.get_active_count(),
            uptime_seconds=uptime,
            memory_usage_mb=round(memory_mb, 2),
            error_count_last_minute=metrics["errors_last_minute"],
            request_count_last_minute=metrics["requests_last_minute"],
            version=API_VERSION,
            spec=OPENENV_SPEC
        )
    except Exception as e:
        logger.error(f"Health check error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Health check failed")


@app.get("/")
async def root():
    """Root endpoint - quick info"""
    request_id = generate_request_id()
    track_request(request_id)
    return {
        "service": "APEX Engineering Benchmark",
        "version": API_VERSION,
        "spec": OPENENV_SPEC,
        "docs": "/docs",
        "health": "/health"
    }


# ============================================================================
# ENDPOINTS - RESET
# ============================================================================

@app.post("/reset", response_model=ResetResponseV2)
async def reset_env(request: ResetRequestV2):
    """
    Reset endpoint - start new episode
    
    Returns:
    - session_id: Use in subsequent /step calls
    - observation: Initial task observation
    """
    request_id = generate_request_id()
    track_request(request_id)
    
    try:
        logger.info(f"[{request_id}] Reset request: domain={request.domain}, difficulty={request.difficulty}")
        
        # Generate session ID if not provided
        session_id = request.session_id or str(uuid4())
        
        # Validate session doesn't already exist
        existing = session_manager.get_session(session_id)
        if existing:
            logger.warning(f"[{request_id}] Session already exists: {session_id}")
            raise HTTPException(
                status_code=409,
                detail=f"Session {session_id} already exists"
            )
        
        # Check session count
        if session_manager.get_active_count() >= MAX_CONCURRENT_SESSIONS:
            logger.error(f"[{request_id}] Max sessions ({MAX_CONCURRENT_SESSIONS}) reached")
            raise HTTPException(
                status_code=429,
                detail=f"Maximum concurrent sessions ({MAX_CONCURRENT_SESSIONS}) reached"
            )
        
        # Select random problem
        task = get_random_problem_by_domain(
            domain=request.domain,
            difficulty=request.difficulty,
            seed=request.seed
        )
        
        if not task:
            logger.error(f"[{request_id}] No task found: {request.domain}/{request.difficulty}")
            raise HTTPException(
                status_code=500,
                detail=f"No task available for {request.domain}/{request.difficulty}"
            )
        
        # Create observation
        observation = PipelineObservationV2(
            task_id=task.get("task_id", "unknown"),
            domain=request.domain,
            task_type=task.get("task_type", "solve"),
            difficulty=request.difficulty,
            title=task.get("title", "Untitled Task"),
            description=task.get("description", ""),
            function_signature=task.get("function_signature"),
            data_sample=task.get("data_sample"),
            current_code=task.get("current_code"),
            error_message=task.get("error_message"),
            incident_report=task.get("incident_report"),
            passed_cases=0,
            total_cases=task.get("visible_test_count", 5) + task.get("hidden_test_count", 3),
            step_count=0,
            max_steps=5
        )
        
        # Create session
        session_manager.create_session(
            session_id=session_id,
            domain=request.domain,
            task_type=task.get("task_type", "solve"),
            task=task
        )
        
        logger.info(f"[{request_id}] Session created: {session_id}")
        
        return ResetResponseV2(
            session_id=session_id,
            observation=observation
        )
    
    except HTTPException:
        track_request(request_id, is_error=True)
        raise
    except Exception as e:
        logger.error(f"[{request_id}] Unexpected error: {e}", exc_info=True)
        track_request(request_id, is_error=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ENDPOINTS - STEP
# ============================================================================

@app.post("/step", response_model=StepResponseV2)
async def step_env(request: StepRequestV2):
    """
    Step endpoint - submit action and get reward
    
    Always returns:
    - observation: Updated task state
    - reward: [0.0, 1.0] float
    - done: True if episode finished
    - info: Breakdown details
    """
    request_id = generate_request_id()
    track_request(request_id)
    
    try:
        logger.info(f"[{request_id}] Step request: session={request.session_id}")
        
        # Get session
        session = session_manager.get_session(request.session_id)
        if not session:
            logger.warning(f"[{request_id}] Session not found: {request.session_id}")
            raise HTTPException(
                status_code=404,
                detail=f"Session {request.session_id} not found or expired"
            )
        
        # Validate at least one action provided
        if not request.code and not request.review and not request.diagnosis:
            logger.warning(f"[{request_id}] No action provided")
            raise HTTPException(
                status_code=400,
                detail="Must provide code, review, or diagnosis"
            )
        
        # Validate action matches task type
        task_type = session["task_type"]
        if task_type == "solve" and not request.code:
            raise HTTPException(status_code=400, detail="code required for solve tasks")
        if task_type == "review" and not request.review:
            raise HTTPException(status_code=400, detail="review required for review tasks")
        if task_type == "debug" and not request.code:
            raise HTTPException(status_code=400, detail="code required for debug tasks")
        
        # Increment step
        session["step_count"] += 1
        truncated = session["step_count"] >= 5  # Max steps
        
        # Calculate reward (simplified - your reward calculator here)
        reward = calculate_reward(session, request)
        session["cumulative_reward"] += reward
        
        done = truncated or False  # Your termination logic
        session["is_terminal"] = done
        
        # Update session
        session_manager.update_session(request.session_id, session)
        
        # Build updated observation
        task = session["task"]
        observation = PipelineObservationV2(
            task_id=task.get("task_id", "unknown"),
            domain=session["domain"],
            task_type=task_type,
            difficulty=task.get("difficulty", "easy"),
            title=task.get("title", ""),
            description=task.get("description", ""),
            passed_cases=session.get("passed_cases", 0),
            total_cases=task.get("visible_test_count", 5) + task.get("hidden_test_count", 3),
            step_count=session["step_count"],
            max_steps=5,
            feedback=f"Step {session['step_count']}/5 completed"
        )
        
        logger.info(f"[{request_id}] Step completed: reward={reward:.3f}, done={done}")
        
        return StepResponseV2(
            session_id=request.session_id,
            observation=observation,
            reward=max(0.0, min(1.0, reward)),  # Clamp to [0, 1]
            done=done,
            truncated=truncated,
            info={
                "step": session["step_count"],
                "cumulative_reward": round(session["cumulative_reward"], 3),
                "reward_breakdown": {"step_reward": round(reward, 3)}
            }
        )
    
    except HTTPException:
        track_request(request_id, is_error=True)
        raise
    except Exception as e:
        logger.error(f"[{request_id}] Unexpected error: {e}", exc_info=True)
        track_request(request_id, is_error=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ENDPOINTS - STATE
# ============================================================================

@app.get("/state/{session_id}", response_model=SessionStateV2)
async def get_state(session_id: str):
    """Get current session state"""
    request_id = generate_request_id()
    track_request(request_id)
    
    try:
        session = session_manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
        
        task = session["task"]
        
        observation = PipelineObservationV2(
            task_id=task.get("task_id", "unknown"),
            domain=session["domain"],
            task_type=session["task_type"],
            difficulty=task.get("difficulty", "easy"),
            title=task.get("title", ""),
            description=task.get("description", ""),
            passed_cases=session.get("passed_cases", 0),
            total_cases=task.get("visible_test_count", 5) + task.get("hidden_test_count", 3),
            step_count=session["step_count"],
            max_steps=5
        )
        
        return SessionStateV2(
            session_id=session_id,
            domain=session["domain"],
            task_type=session["task_type"],
            difficulty=task.get("difficulty", "easy"),
            current_step=session["step_count"],
            max_steps=5,
            cumulative_reward=round(session["cumulative_reward"], 3),
            is_terminal=session["is_terminal"],
            created_at=datetime.utcnow(),
            last_action_at=datetime.utcnow(),
            observation=observation
        )
    
    except HTTPException:
        track_request(request_id, is_error=True)
        raise
    except Exception as e:
        logger.error(f"[{request_id}] Error: {e}", exc_info=True)
        track_request(request_id, is_error=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def calculate_reward(session: Dict, request: StepRequestV2) -> float:
    """Calculate reward - placeholder, replace with your logic"""
    import random
    
    task_type = session["task_type"]
    step = session["step_count"]
    difficulty = session["task"].get("difficulty", "easy")
    
    # Difficulty modifier
    base_reward = {
        "easy": 0.8,
        "medium": 0.6,
        "hard": 0.4
    }.get(difficulty, 0.5)
    
    # Step penalty
    step_penalty = step * 0.05
    
    # Effort reward (simplified)
    if request.code:
        effort_bonus = 0.1 if len(request.code) > 50 else 0.05
    else:
        effort_bonus = 0.0
    
    reward = base_reward - step_penalty + effort_bonus + random.uniform(0, 0.1)
    return max(0.0, min(1.0, reward))


# ============================================================================
# STARTUP & SHUTDOWN
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """On startup"""
    logger.info(f"🚀 APEX API Started - v{API_VERSION} ({OPENENV_SPEC})")
    logger.info(f"Max concurrent sessions: {MAX_CONCURRENT_SESSIONS}")
    logger.info(f"Session timeout: {SESSION_TIMEOUT_SECONDS}s")


@app.on_event("shutdown")
async def shutdown_event():
    """On shutdown"""
    logger.info("🛑 APEX API Shutting down")
    logger.info(f"Total requests: {request_metrics['total_requests']}")
    logger.info(f"Total errors: {request_metrics['total_errors']}")
