"""FastAPI Server for APEX Code Solver Environment - All endpoints"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
import json
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, WebSocket, HTTPException, Query, Body, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from models import (
    CodeAction, ResetResponse, StepResponse, EnvState,
    ManifestResponse, ProblemsListResponse, ProblemDetail,
    SessionListResponse, SessionInfo, LeaderboardResponse, LeaderboardEntry,
    ProblemObservation, TestCaseResult, EvaluateRequest, EvaluationReport,
    ProblemScore
)
from .code_solver_environment import CodeSolverEnvironment
from .streaming import (
    stream_step_response_sse, WebSocketMessageBuilder
)
from .problems import CANONICAL_PROBLEMS, get_problem_by_id

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Global environment instance
env = CodeSolverEnvironment()

# Application
app = FastAPI(
    title="APEX Code Solver",
    description="RL Environment for solving coding problems - Multi-session with sandboxing",
    version="2.0.0",
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
# HEALTH & INFO ENDPOINTS
# ============================================================================

@app.get("/health")
async def health():
    """Health check endpoint"""
    sessions = await env.session_manager.get_active_sessions()
    return {
        "status": "ok",
        "active_sessions": len(sessions),
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/progress/{session_id}")
async def get_progress(session_id: str):
    """Get curriculum learning progress for an agent/session"""
    try:
        progress = await env.curriculum.get_progress(session_id)
        return {
            "status": "ok",
            "data": progress
        }
    except Exception as e:
        logger.error(f"Error getting progress: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
async def root():
    """Root endpoint with service info"""
    return {
        "service": "APEX Code Solver",
        "version": "2.0.0",
        "spec": "openenv/v1",
        "contact": "Team APEX"
    }


# ============================================================================
# MANIFEST & DISCOVERY
# ============================================================================

@app.get("/manifest", response_model=ManifestResponse)
async def manifest():
    """Get environment manifest for auto-discovery and configuration."""
    return ManifestResponse(
        name="code_solver",
        version="2.0.0",
        spec="openenv/v1",
        description="RL environment for training agents to solve LeetCode-style coding problems with online test evaluation and partial credit rewards",
        contact="Team APEX",
        action_schema={
            "type": "object",
            "properties": {
                "code": {"type": "string", "description": "Python solution code"},
                "session_id": {"type": ["string", "null"], "description": "Optional session ID"}
            },
            "required": ["code"]
        },
        observation_schema={
            "type": "object",
            "properties": {
                "problem_id": {"type": "string"},
                "title": {"type": "string"},
                "description": {"type": "string"},
                "function_signature": {"type": "string"},
                "examples": {"type": "string"},
                "constraints": {"type": "string"},
                "difficulty": {"type": "string", "enum": ["easy", "medium", "hard"]},
                "test_results": {"type": "array"},
                "passed_cases": {"type": "integer"},
                "total_cases": {"type": "integer"},
                "step_count": {"type": "integer"},
                "max_steps": {"type": "integer"}
            }
        },
        transport=["http", "websocket"],
        endpoints={
            "reset": "POST /reset",
            "step": "POST /step",
            "step_stream": "POST /step/stream",
            "state": "GET /state",
            "websocket": "WS /ws/{session_id}",
            "health": "GET /health",
            "manifest": "GET /manifest",
            "problems": "GET /problems",
            "leaderboard": "GET /leaderboard",
            "sessions": "GET /sessions"
        },
        reward={
            "min": 0.0,
            "max": 1.0,
            "type": "continuous",
            "description": "Reward = (passed_cases/total) + efficiency_bonus + attempt_penalty, clipped to [0,1]"
        },
        problems={
            "canonical": len(CANONICAL_PROBLEMS),
            "procedural": "infinite",
            "difficulties": ["easy", "medium", "hard"]
        },
        capabilities=[
            "multi_session",
            "procedural_generation",
            "sandboxed_execution",
            "websocket",
            "seed_control",
            "streaming",
            "reward_shaping"
        ]
    )


# ============================================================================
# TASKS ENDPOINT
# ============================================================================

@app.get("/tasks")
async def list_tasks():
    """List available task templates for judges and automated testing."""
    return {
        "tasks": [
            {
                "id": "easy-solve",
                "difficulty": "easy",
                "mode": "solve",
                "description": "Write Python code to solve easy coding problems"
            },
            {
                "id": "medium-solve",
                "difficulty": "medium",
                "mode": "solve",
                "description": "Write Python code to solve medium coding problems"
            },
            {
                "id": "hard-solve",
                "difficulty": "hard",
                "mode": "solve",
                "description": "Write Python code to solve hard coding problems"
            },
            {
                "id": "easy-review",
                "difficulty": "easy",
                "mode": "review",
                "description": "Find and fix bugs in easy Python code"
            },
            {
                "id": "medium-review",
                "difficulty": "medium",
                "mode": "review",
                "description": "Find and fix bugs in medium Python code"
            },
            {
                "id": "hard-review",
                "difficulty": "hard",
                "mode": "review",
                "description": "Find and fix bugs in hard Python code"
            }
        ]
    }


# ============================================================================
# RESET ENDPOINT
# ============================================================================

class ResetRequest(BaseModel):
    """Reset endpoint request body"""
    session_id: Optional[str] = None
    difficulty: Optional[str] = None
    mode: str = "solve"  # solve or review
    problem_source: str = "mixed"  # canonical, procedural, mixed
    seed: Optional[int] = None

@app.post("/reset", response_model=ResetResponse)
async def reset_env(request: ResetRequest):
    """Reset environment and get initial observation."""
    try:
        new_session_id, observation = await env.reset(
            session_id=request.session_id,
            difficulty=request.difficulty,
            mode=request.mode,
            seed=request.seed,
            problem_source=request.problem_source
        )

        return ResetResponse(
            session_id=new_session_id,
            observation=observation
        )
    except Exception as e:
        logger.error(f"Reset error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# STEP ENDPOINTS
# ============================================================================

@app.post("/step", response_model=StepResponse)
async def step_env(
    action: CodeAction,
    session_id: Optional[str] = Query(None, description="Session ID (from reset)")
):
    """Execute code and return step results."""
    try:
        # Get session ID from query or body
        sid = session_id or action.session_id
        if not sid:
            raise ValueError("session_id required in query or body")

        observation, reward, terminated, truncated, info = await env.step(
            session_id=sid,
            code=action.code
        )

        return StepResponse(
            session_id=sid,
            observation=observation,
            reward=reward,
            terminated=terminated,
            truncated=truncated,
            info=info
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Step error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/step/stream")
async def step_stream(
    action: CodeAction,
    session_id: Optional[str] = Query(None)
):
    """Execute code with streaming results via Server-Sent Events (SSE)."""
    try:
        sid = session_id or action.session_id
        if not sid:
            raise ValueError("session_id required")

        observation, reward, terminated, truncated, info = await env.step(
            session_id=sid,
            code=action.code
        )

        # Build test results list for streaming
        test_results = []
        if observation.test_results:
            test_results = [
                {
                    "case_index": r.case_index,
                    "passed": r.passed,
                    "error": r.error,
                    "time_ms": r.time_ms
                }
                for r in observation.test_results
            ]

        obs_dict = observation.model_dump()

        async def generate():
            async for event in stream_step_response_sse(
                test_results=test_results,
                observation=obs_dict,
                reward=reward,
                terminated=terminated,
                truncated=truncated,
                info=info
            ):
                yield event

        return StreamingResponse(
            generate(),
            media_type="text/event-stream"
        )
    except Exception as e:
        logger.error(f"Stream error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# STATE ENDPOINT
# ============================================================================

@app.get("/state", response_model=EnvState)
async def get_state(session_id: str = Query(..., description="Session ID")):
    """Get current session state."""
    try:
        state = await env.get_state(session_id=session_id)
        return state
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Get state error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# SESSION MANAGEMENT
# ============================================================================

@app.get("/sessions", response_model=SessionListResponse)
async def list_sessions():
    """Get all active sessions"""
    try:
        sessions = await env.session_manager.get_active_sessions()
        return SessionListResponse(
            active_count=len(sessions),
            sessions=sessions
        )
    except Exception as e:
        logger.error(f"List sessions error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete a session explicitly"""
    try:
        deleted = await env.session_manager.delete_session(session_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Session not found")
        return {"status": "deleted", "session_id": session_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete session error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# PROBLEMS ENDPOINTS
# ============================================================================

@app.get("/problems", response_model=ProblemsListResponse)
async def list_problems(difficulty: Optional[str] = Query(None)):
    """List available problems"""
    try:
        problems = CANONICAL_PROBLEMS
        if difficulty:
            problems = [p for p in problems if p["difficulty"] == difficulty]

        problem_details = [
            ProblemDetail(
                problem_id=p["problem_id"],
                title=p["title"],
                description=p["description"],
                function_signature=p["function_signature"],
                examples=p["examples"],
                constraints=p["constraints"],
                difficulty=p["difficulty"],
                total_cases=len(p["test_cases"]),
                source=p.get("source", "canonical")
            )
            for p in problems
        ]

        return ProblemsListResponse(
            total=len(problem_details),
            canonical=len(problems),
            procedural="infinite",
            problems=problem_details
        )
    except Exception as e:
        logger.error(f"List problems error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/problems/{problem_id}")
async def get_problem(problem_id: str):
    """Get a single problem detail (without test cases)"""
    try:
        problem = get_problem_by_id(problem_id)
        if not problem:
            raise HTTPException(status_code=404, detail="Problem not found")

        return {
            "problem_id": problem["problem_id"],
            "title": problem["title"],
            "description": problem["description"],
            "function_signature": problem["function_signature"],
            "examples": problem["examples"],
            "constraints": problem["constraints"],
            "difficulty": problem["difficulty"],
            "total_cases": len(problem.get("test_cases", [])),
            "source": problem.get("source", "canonical")
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get problem error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# LEADERBOARD
# ============================================================================

@app.get("/leaderboard", response_model=LeaderboardResponse)
async def get_leaderboard(problem_id: Optional[str] = Query(None)):
    """Get leaderboard of best rewards."""
    try:
        entries_raw = env.session_manager.get_leaderboard(problem_id)

        entries = [
            LeaderboardEntry(
                rank=i + 1,
                problem_id=e.get("session_id", "unknown"),
                problem_title="Unknown",
                reward=e.get("reward", 0.0),
                session_id=e.get("session_id", ""),
                timestamp=e.get("timestamp", datetime.utcnow())
            )
            for i, e in enumerate(entries_raw)
        ]

        return LeaderboardResponse(
            problem_id=problem_id,
            entries=entries,
            count=len(entries)
        )
    except Exception as e:
        logger.error(f"Leaderboard error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# EVALUATION ENDPOINT (for benchmarking agents)
# ============================================================================

@app.post("/evaluate", response_model=EvaluationReport)
async def evaluate_agent(request: EvaluateRequest):
    """
    Evaluate an agent's solutions across multiple problems.
    
    This endpoint is used by judges/researchers to benchmark agent performance
    across the entire problem set with a comprehensive scoring report.
    """
    try:
        from .sandbox import execute_code_sandboxed
        from .rewards import RewardCalculator
        
        problem_scores: dict[str, ProblemScore] = {}
        difficulty_scores = {"easy": [], "medium": [], "hard": []}
        all_rewards = []
        
        # Get all canonical problems for evaluation
        canonical_problems = CANONICAL_PROBLEMS[:9]  # Use first 9 canonical problems
        
        for problem in canonical_problems:
            problem_id = problem["problem_id"]
            
            # Skip if agent didn't provide solution for this problem
            if problem_id not in request.agent_solutions:
                logger.warning(f"Agent did not provide solution for {problem_id}")
                problem_scores[problem_id] = ProblemScore(
                    problem_id=problem_id,
                    title=problem["title"],
                    difficulty=problem["difficulty"],
                    passed_cases=0,
                    total_cases=len(problem["test_cases"]),
                    reward=0.0,
                    explanation="No solution provided for this problem"
                )
                all_rewards.append(0.0)
                difficulty_scores[problem["difficulty"]].append(0.0)
                continue
            
            agent_code = request.agent_solutions[problem_id]
            
            # Extract function name from signature
            sig = problem["function_signature"]
            func_name = sig.split("(")[0].replace("def ", "").strip()
            
            # Execute code against test cases using sandbox
            try:
                result = execute_code_sandboxed(
                    code=agent_code,
                    test_cases=problem["test_cases"],
                    func_name=func_name,
                    timeout=10
                )
                
                test_results = result.get("results", [])
                passed_count = sum(1 for r in test_results if r.get("passed", False))
                error = result.get("error")
                execution_time_ms = sum(r.get("time_ms", 0.0) for r in test_results)
                
            except Exception as e:
                logger.error(f"Error evaluating {problem_id}: {e}")
                test_results = []
                passed_count = 0
                error = str(e)
                execution_time_ms = 0.0
            
            # Calculate reward
            reward_data = RewardCalculator.calculate(
                passed_cases=passed_count,
                total_cases=len(problem["test_cases"]),
                time_ms_total=execution_time_ms,
                step_count=1,
                code_lines=len(agent_code.split("\n")),
                test_results=test_results,
                error_message=error
            )
            
            reward = reward_data["reward"]
            all_rewards.append(reward)
            difficulty_scores[problem["difficulty"]].append(reward)
            
            # Explanation
            if passed_count == len(problem["test_cases"]):
                explanation = f"Perfect: {passed_count}/{len(problem['test_cases'])} tests passed in {execution_time_ms:.0f}ms"
            elif passed_count > 0:
                explanation = f"Partial: {passed_count}/{len(problem['test_cases'])} tests passed"
            else:
                explanation = f"Failed: {error or 'all tests failed'}"
            
            problem_scores[problem_id] = ProblemScore(
                problem_id=problem_id,
                title=problem["title"],
                difficulty=problem["difficulty"],
                passed_cases=passed_count,
                total_cases=len(problem["test_cases"]),
                reward=reward,
                explanation=explanation
            )
        
        # Calculate average by difficulty
        by_difficulty = {}
        for diff in ["easy", "medium", "hard"]:
            scores = difficulty_scores[diff]
            by_difficulty[diff] = round(sum(scores) / len(scores), 3) if scores else 0.0
        
        # Overall score
        total_score = round(sum(all_rewards) / len(all_rewards), 3) if all_rewards else 0.0
        
        # Determine rank
        if total_score >= 0.9:
            rank = "expert"
            feedback = "Exceptional performance! Solves complex problems with optimal solutions. Ready for production RL training."
        elif total_score >= 0.75:
            rank = "advanced"
            feedback = f"Strong solver. Excels at {', '.join([d for d in ['easy', 'medium', 'hard'] if by_difficulty[d] >= 0.8])} problems. May struggle with complex DP or graph algorithms."
        elif total_score >= 0.50:
            rank = "intermediate"
            feedback = f"Decent performance on easier problems ({by_difficulty['easy']:.2f}). Struggles with hard problems ({by_difficulty['hard']:.2f}). Recommend: practice advanced data structures and algorithm strategies."
        else:
            rank = "beginner"
            feedback = "Foundation level. Focus on understanding basic algorithms before attempting complex problems. Start with easy problems."
        
        return EvaluationReport(
            total_score=total_score,
            by_difficulty=by_difficulty,
            by_problem=problem_scores,
            rank=rank,
            feedback=feedback,
            timestamp=datetime.utcnow().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Evaluation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(e)}")


# ============================================================================
# WEBSOCKET ENDPOINT
# ============================================================================

active_connections: dict = {}


@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for persistent connection."""
    await websocket.accept()
    active_connections[session_id] = websocket

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            msg_type = message.get("type")

            try:
                if msg_type == "reset":
                    new_session_id, observation = await env.reset(
                        session_id=session_id,
                        difficulty=message.get("difficulty"),
                        mode=message.get("mode", "mixed"),
                        seed=message.get("seed")
                    )

                    response = WebSocketMessageBuilder.reset_response_event(
                        session_id=new_session_id,
                        observation=observation.model_dump()
                    )
                    await websocket.send_json(response)

                elif msg_type == "step":
                    code = message.get("code", "")
                    observation, reward, terminated, truncated, info = await env.step(
                        session_id=session_id,
                        code=code
                    )

                    response = WebSocketMessageBuilder.step_response_event(
                        session_id=session_id,
                        observation=observation.model_dump(),
                        reward=reward,
                        terminated=terminated,
                        truncated=truncated,
                        info=info
                    )
                    await websocket.send_json(response)

                else:
                    error_msg = WebSocketMessageBuilder.error_event(
                        "INVALID_MESSAGE",
                        f"Unknown message type: {msg_type}"
                    )
                    await websocket.send_json(error_msg)

            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                error_msg = WebSocketMessageBuilder.error_event(
                    "EXECUTION_ERROR",
                    str(e)
                )
                await websocket.send_json(error_msg)

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {session_id}")
        if session_id in active_connections:
            del active_connections[session_id]
    except Exception as e:
        logger.error(f"WebSocket fatal error: {e}")
        if session_id in active_connections:
            del active_connections[session_id]


@app.get("/ws/health")
async def websocket_health():
    """Health check for WebSocket connections"""
    return {
        "active_websocket_connections": len(active_connections),
        "timestamp": datetime.utcnow().isoformat()
    }
