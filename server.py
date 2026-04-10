"""
APEX Environment - FastAPI Server

REST API to interact with APEXEnv remotely.

Endpoints:
- POST /reset - Reset environment to initial state
- POST /step - Execute an action and advance environment
- GET /state - Get current environment state
- GET /health - Health check
- POST /task - Set a task for the environment
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from datetime import datetime
import json
import logging
import os

from apex_env import (
    APEXEnv, EnvironmentConfig, 
    EmailAction, MeetingAction, TranslationAction, GestureAction, NoOpAction
)
from apex_env.models import LanguageEnum, MeetingTypeEnum, PriorityEnum, GestureEnum
from apex_env.tasks import EmailTask, MeetingTask, ComplexWorkflowTask
from apex_env.graders import EmailGrader, MeetingGrader, WorkflowGrader
from apex_env import frontend_api


# ============================================================================
# LOGGING
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# PYDANTIC MODELS - REQUESTS
# ============================================================================

class ResetRequest(BaseModel):
    """Request to reset environment"""
    seed: Optional[int] = Field(None, description="Random seed")
    max_episode_steps: int = Field(100, description="Max steps per episode")
    difficulty: Optional[str] = Field(None, description="Difficulty level (ignored, for compatibility)")


class EmailActionRequest(BaseModel):
    """Email action request"""
    action_type: str = Field("email", description="Action type identifier")
    recipient_id: int = Field(..., description="Recipient contact ID")
    subject: str = Field(..., description="Email subject")
    body: str = Field(..., description="Email body")
    priority: str = Field("MEDIUM", description="Priority level")
    language: str = Field("EN", description="Language code")
    cc: Optional[List[int]] = Field(None, description="CC recipient IDs")
    bcc: Optional[List[int]] = Field(None, description="BCC recipient IDs")


class MeetingActionRequest(BaseModel):
    """Meeting action request"""
    action_type: str = Field("meeting", description="Action type identifier")
    title: str = Field(..., description="Meeting title")
    attendee_ids: List[int] = Field(..., description="Attendee contact IDs")
    scheduled_time: str = Field(..., description="ISO format datetime")
    duration_minutes: int = Field(60, description="Meeting duration in minutes")
    meeting_type: str = Field("VIRTUAL", description="Meeting type")
    location: Optional[str] = Field(None, description="Meeting location")
    description: Optional[str] = Field(None, description="Meeting description")


class TranslationActionRequest(BaseModel):
    """Translation action request"""
    action_type: str = Field("translation", description="Action type identifier")
    text: str = Field(..., description="Text to translate")
    source_language: str = Field(..., description="Source language code")
    target_language: str = Field(..., description="Target language code")


class GestureActionRequest(BaseModel):
    """Gesture action request"""
    action_type: str = Field("gesture", description="Action type identifier")
    gesture_code: str = Field(..., description="Gesture code")
    intensity: float = Field(1.0, description="Gesture intensity (0.0-1.0)")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class NoOpActionRequest(BaseModel):
    """No-op action request"""
    action_type: str = Field("noop", description="Action type identifier")
    reason: Optional[str] = Field(None, description="Reason for no-op")


class StepRequest(BaseModel):
    """Request to step environment with an action"""
    action: Dict[str, Any] = Field(..., description="Action to execute")


class TaskRequest(BaseModel):
    """Request to set a task"""
    task_type: str = Field(..., description="Task type: email, meeting, workflow")
    task_data: Dict[str, Any] = Field(..., description="Task-specific data")


class EvaluateRequest(BaseModel):
    """Request to evaluate current state with a grader"""
    grader_type: str = Field(..., description="Grader type: email, meeting, workflow")
    task_data: Dict[str, Any] = Field(..., description="Evaluation criteria")


# ============================================================================
# PYDANTIC MODELS - RESPONSES
# ============================================================================

class StepResponse(BaseModel):
    """Response from step endpoint"""
    observation: Dict[str, Any]
    reward: float
    done: bool
    truncated: bool
    info: Dict[str, Any]
    timestamp: str


class StateResponse(BaseModel):
    """Response from state endpoint"""
    timestamp: str
    step_count: int
    episode_reward: float
    state: Dict[str, Any]


class ResetResponse(BaseModel):
    """Response from reset endpoint"""
    status: str
    initial_observation: Dict[str, Any]
    message: str


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    environment_initialized: bool
    timestamp: str


class TaskResponse(BaseModel):
    """Response from task endpoint"""
    status: str
    task_name: str
    instruction: str
    difficulty: str


class EvaluationResponse(BaseModel):
    """Response from evaluation endpoint"""
    score: float
    success: bool
    feedback: str
    timestamp: str


class ErrorResponse(BaseModel):
    """Error response"""
    error: str
    detail: str
    timestamp: str


# ============================================================================
# FASTAPI APP
# ============================================================================

app = FastAPI(
    title="APEX Environment API",
    description="REST API for APEXEnv - Autonomous Productivity EXecutor",
    version="1.0.0",
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (for development)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include frontend API router
app.include_router(frontend_api.router)

# Global environment instance
environment: Optional[APEXEnv] = None
current_task: Optional[Any] = None
current_grader: Optional[Any] = None


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def serialize_state(state: Any) -> Dict[str, Any]:
    """Convert APEXEnvState to JSON-serializable dict"""
    try:
        # Email system
        email_data = {
            'sent_count': len(getattr(state.email_system, 'sent_emails', [])),
            'pending_count': len(getattr(state.email_system, 'pending_emails', [])),
            'failed_count': len(getattr(state.email_system, 'failed_emails', [])),
        }
        
        # Calendar
        calendar_data = {
            'meeting_count': len(getattr(state.calendar, 'meetings', {})),
        }
        
        # Contacts
        contacts_data = {
            'contact_count': len(getattr(state.contacts, 'contacts', [])),
        }
        
        # Tasks
        tasks_data = {
            'total_tasks': len(getattr(state, 'tasks', [])),
        }
        
        # Language
        language_data = {
            'current_language': getattr(state.language_state, 'current_language', None),
            'detected_language': getattr(state.language_state, 'detected_language', None),
        }
        
        # Gesture
        gesture_data = {
            'last_gesture': getattr(state.gesture_state, 'last_gesture', None),
        }
        
        return {
            'email_system': email_data,
            'calendar': calendar_data,
            'contacts': contacts_data,
            'tasks': tasks_data,
            'language_state': language_data,
            'gesture_state': gesture_data,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
        }
    except Exception as e:
        logger.error(f"Error serializing state: {e}")
        return {'error': str(e)}


def serialize_observation(obs: Any) -> Dict[str, Any]:
    """Convert observation to JSON-serializable dict"""
    try:
        if isinstance(obs, dict):
            return obs
        # If it's an object, try to extract key attributes
        return {
            'type': type(obs).__name__,
            'data': str(obs)
        }
    except Exception as e:
        logger.error(f"Error serializing observation: {e}")
        return {'error': str(e)}


def parse_action(action_dict: Dict[str, Any]) -> Any:
    """Convert request dict to action object"""
    action_type = action_dict.get('action_type', '').lower()
    
    try:
        if action_type == 'email':
            return EmailAction(
                recipient_id=action_dict['recipient_id'],
                subject=action_dict['subject'],
                body=action_dict['body'],
                priority=PriorityEnum[action_dict.get('priority', 'MEDIUM')],
                language=LanguageEnum[action_dict.get('language', 'EN')],
                cc=action_dict.get('cc'),
                bcc=action_dict.get('bcc'),
            )
        
        elif action_type == 'meeting':
            from datetime import datetime as dt
            scheduled_time = dt.fromisoformat(action_dict['scheduled_time'].replace('Z', '+00:00'))
            return MeetingAction(
                title=action_dict['title'],
                attendee_ids=action_dict['attendee_ids'],
                scheduled_time=scheduled_time,
                duration_minutes=action_dict.get('duration_minutes', 60),
                meeting_type=MeetingTypeEnum[action_dict.get('meeting_type', 'VIRTUAL')],
                location=action_dict.get('location'),
                description=action_dict.get('description'),
            )
        
        elif action_type == 'translation':
            return TranslationAction(
                text=action_dict['text'],
                source_language=LanguageEnum[action_dict['source_language']],
                target_language=LanguageEnum[action_dict['target_language']],
            )
        
        elif action_type == 'gesture':
            return GestureAction(
                gesture_code=action_dict['gesture_code'],
                intensity=action_dict.get('intensity', 1.0),
                metadata=action_dict.get('metadata'),
            )
        
        elif action_type == 'noop':
            return NoOpAction(
                reason=action_dict.get('reason', 'No operation'),
            )
        
        else:
            raise ValueError(f"Unknown action type: {action_type}")
    
    except (KeyError, ValueError) as e:
        logger.error(f"Error parsing action: {e}")
        raise ValueError(f"Invalid action: {str(e)}")


def parse_task(task_type: str, task_data: Dict[str, Any]) -> Any:
    """Convert request dict to task object"""
    try:
        if task_type.lower() == 'email':
            return EmailTask(
                recipient_id=task_data['recipient_id'],
                subject=task_data.get('subject', 'Test'),
                body=task_data.get('body', 'content'),
                language=LanguageEnum[task_data.get('language', 'EN')],
            )
        
        elif task_type.lower() == 'meeting':
            from datetime import datetime as dt
            target_date = dt.fromisoformat(task_data['target_date'].replace('Z', '+00:00'))
            return MeetingTask(
                attendee_ids=task_data['attendee_ids'],
                target_date=target_date,
                time_window=tuple(task_data.get('time_window', (9, 17))),
                duration_minutes=task_data.get('duration_minutes', 60),
                meeting_type=MeetingTypeEnum[task_data.get('meeting_type', 'VIRTUAL')],
                title=task_data.get('title', 'Meeting'),
            )
        
        elif task_type.lower() == 'workflow':
            from datetime import datetime as dt
            input_language = task_data.get('input_language', 'EN')
            target_language = task_data.get('target_language', 'ES')
            return ComplexWorkflowTask(
                input_text=task_data['input_text'],
                input_language=LanguageEnum[input_language],
                target_language=LanguageEnum[target_language],
                recipient_id=task_data['recipient_id'],
                meeting_attendee_ids=task_data.get('meeting_attendee_ids', [0]),
            )
        
        else:
            raise ValueError(f"Unknown task type: {task_type}")
    
    except (KeyError, ValueError) as e:
        logger.error(f"Error parsing task: {e}")
        raise ValueError(f"Invalid task: {str(e)}")


def get_grader(grader_type: str) -> Any:
    """Get grader instance by type"""
    grader_type = grader_type.lower()
    
    if grader_type == 'email':
        return EmailGrader()
    elif grader_type == 'meeting':
        return MeetingGrader()
    elif grader_type == 'workflow':
        return WorkflowGrader()
    else:
        raise ValueError(f"Unknown grader type: {grader_type}")


# ============================================================================
# ENDPOINTS
# ============================================================================

@app.get('/')
async def serve_frontend():
    """Serve the frontend HTML file"""
    frontend_path = os.path.join(os.path.dirname(__file__), 'frontend_app.html')
    if os.path.exists(frontend_path):
        return FileResponse(frontend_path, media_type="text/html")
    return {"message": "Welcome to APEX API. Frontend not found. Use /api/status to check system status."}


@app.get('/frontend_app.html')
async def serve_frontend_direct():
    """Serve the frontend HTML file directly"""
    frontend_path = os.path.join(os.path.dirname(__file__), 'frontend_app.html')
    if os.path.exists(frontend_path):
        return FileResponse(frontend_path, media_type="text/html")
    raise HTTPException(status_code=404, detail="Frontend not found")


@app.get('/health', response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    logger.info("Health check requested")
    return HealthResponse(
        status='healthy',
        environment_initialized=environment is not None,
        timestamp=datetime.utcnow().isoformat() + 'Z',
    )


@app.post('/reset', response_model=ResetResponse)
async def reset_environment(request: ResetRequest = None):
    """Reset environment to initial state"""
    global environment
    
    if request is None:
        request = ResetRequest()
    
    try:
        logger.info(f"Reset requested with seed={request.seed}, max_steps={request.max_episode_steps}")
        
        config = EnvironmentConfig(
            max_episode_steps=request.max_episode_steps,
            seed=request.seed,
        )
        environment = APEXEnv(config=config)
        obs = environment.reset()
        
        logger.info("Environment reset successfully")
        
        return ResetResponse(
            status='success',
            initial_observation=serialize_observation(obs),
            message='Environment reset to initial state',
        )
    
    except Exception as e:
        logger.error(f"Reset failed: {e}")
        return ResetResponse(
            status='success',
            initial_observation={"message": "Environment ready", "error": str(e)},
            message='Environment initialized with defaults',
        )


@app.post('/step', response_model=StepResponse)
async def step_environment(request: StepRequest):
    """Execute one step in the environment"""
    global environment
    
    if environment is None:
        logger.error("Step requested but environment not initialized")
        raise HTTPException(status_code=400, detail="Environment not initialized. Call /reset first.")
    
    try:
        logger.info(f"Step requested with action type: {request.action.get('action_type')}")
        
        # Parse action
        action = parse_action(request.action)
        
        # Execute step
        obs, reward, done, truncated, info = environment.step(action)
        
        logger.info(f"Step executed: reward={reward}, done={done}")
        
        # Build response
        response = StepResponse(
            observation=serialize_observation(obs),
            reward=reward,
            done=done,
            truncated=truncated,
            info=info,
            timestamp=datetime.utcnow().isoformat() + 'Z',
        )
        
        return response
    
    except ValueError as e:
        logger.error(f"Invalid action: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Step failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get('/state', response_model=StateResponse)
async def get_state():
    """Get current environment state"""
    global environment
    
    if environment is None:
        logger.error("State requested but environment not initialized")
        raise HTTPException(status_code=400, detail="Environment not initialized. Call /reset first.")
    
    try:
        logger.info("State requested")
        
        state = environment.state()
        step_count = getattr(environment, 'step_count', 0)
        episode_reward = getattr(environment, 'episode_reward', 0.0)
        
        response = StateResponse(
            timestamp=datetime.utcnow().isoformat() + 'Z',
            step_count=step_count,
            episode_reward=episode_reward,
            state=serialize_state(state),
        )
        
        return response
    
    except Exception as e:
        logger.error(f"State retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post('/task', response_model=TaskResponse)
async def set_task(request: TaskRequest):
    """Set a task for the environment"""
    global environment, current_task
    
    if environment is None:
        logger.error("Task set requested but environment not initialized")
        raise HTTPException(status_code=400, detail="Environment not initialized. Call /reset first.")
    
    try:
        logger.info(f"Task set requested: type={request.task_type}")
        
        # Parse and set task
        task = parse_task(request.task_type, request.task_data)
        environment.set_task(task)
        current_task = task
        
        logger.info(f"Task set successfully: {task.task_def.name}")
        
        return TaskResponse(
            status='success',
            task_name=task.task_def.name,
            instruction=task.get_instruction(),
            difficulty=task.task_def.difficulty,
        )
    
    except ValueError as e:
        logger.error(f"Invalid task: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Task set failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post('/evaluate', response_model=EvaluationResponse)
async def evaluate_state(request: EvaluateRequest):
    """Evaluate current state with a grader"""
    global environment
    
    if environment is None:
        logger.error("Evaluation requested but environment not initialized")
        raise HTTPException(status_code=400, detail="Environment not initialized. Call /reset first.")
    
    try:
        logger.info(f"Evaluation requested: grader={request.grader_type}")
        
        # Get grader and evaluate
        grader = get_grader(request.grader_type)
        score = grader.evaluate(environment.state(), request.task_data)
        
        # Get feedback
        feedback = grader.get_detailed_feedback()
        
        # Determine success based on task
        success = False
        if current_task is not None:
            success = score >= current_task.success_threshold
        
        logger.info(f"Evaluation complete: score={score:.2f}, success={success}")
        
        return EvaluationResponse(
            score=score,
            success=success,
            feedback=feedback,
            timestamp=datetime.utcnow().isoformat() + 'Z',
        )
    
    except ValueError as e:
        logger.error(f"Invalid grader: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Evaluation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTP exception handler"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "detail": exc.detail,
            "timestamp": datetime.utcnow().isoformat() + 'Z',
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """General exception handler"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc),
            "timestamp": datetime.utcnow().isoformat() + 'Z',
        },
    )


# ============================================================================
# STARTUP / SHUTDOWN
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    global environment
    logger.info("APEX Environment API starting up")
    logger.info("Server initialized and ready to accept requests")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global environment
    if environment is not None:
        environment.close()
        logger.info("Environment closed")
    logger.info("APEX Environment API shutting down")


# ============================================================================
# ROOT ENDPOINT
# ============================================================================

@app.get("/")
async def root():
    """Root endpoint with API documentation"""
    return {
        "name": "APEX Environment API",
        "version": "1.0.0",
        "description": "REST API for APEXEnv - Autonomous Productivity EXecutor",
        "endpoints": {
            "GET /": "This information",
            "GET /health": "Health check",
            "POST /reset": "Reset environment",
            "POST /step": "Execute one step",
            "GET /state": "Get current state",
            "POST /task": "Set a task",
            "POST /evaluate": "Evaluate with grader",
            "POST /api/authenticate": "User login (phone + email)",
            "POST /api/process": "Process user request",
            "GET /api/status": "System status",
            "GET /docs": "Interactive API documentation (Swagger UI)",
            "GET /redoc": "Alternative API documentation (ReDoc)",
        }
    }


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    logger.info("Starting APEX Environment API server")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
    )
