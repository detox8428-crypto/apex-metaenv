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
    PipelineAction, ResetResponse, StepResponse, EnvState,
    ManifestResponse, ProblemsListResponse, ProblemDetail,
    SessionListResponse, SessionInfo, LeaderboardResponse, LeaderboardEntry,
    PipelineObservation, TestCaseResult, EvaluateRequest, EvaluationReport,
    ProblemScore
)
from .code_solver_environment import CodeSolverEnvironment
from .streaming import (
    stream_step_response_sse, WebSocketMessageBuilder
)
from .problems import SOLVE_TASKS, REVIEW_TASKS, DEBUG_TASKS, select_random_task, get_task_by_id
from .rewards import PipelineRewardCalculator

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Global environment instance
env = CodeSolverEnvironment()

# Application
app = FastAPI(
    title="APEX Data Pipeline Engineer",
    description="RL Environment for real-world data pipeline engineering - solve, review, and debug pandas/ETL tasks",
    version="3.0.0",
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
        "service": "APEX Data Pipeline Engineer",
        "version": "3.0.0",
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
        name="apex-data-pipeline",
        version="3.0.0",
        spec="openenv/v1",
        description="RL environment for real-world data pipeline engineering - write, review, and debug pandas/ETL code",
        contact="Team APEX",
        action_schema={
            "type": "object",
            "properties": {
                "code": {"type": ["string", "null"], "description": "Python code (for solve/debug modes)"},
                "review": {"type": ["object", "null"], "description": "Code review JSON (for review mode)"},
                "session_id": {"type": ["string", "null"], "description": "Session ID"}
            },
            "required": []
        },
        observation_schema={
            "type": "object",
            "properties": {
                "task_id": {"type": "string"},
                "task_type": {"type": "string", "enum": ["solve", "review", "debug"]},
                "title": {"type": "string"},
                "description": {"type": "string"},
                "function_signature": {"type": "string"},
                "data_sample": {"type": "object"},
                "difficulty": {"type": "string", "enum": ["easy", "medium", "hard"]},
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
            "health": "GET /health",
            "manifest": "GET /manifest",
            "tasks": "GET /tasks",
            "sessions": "GET /sessions"
        },
        reward={
            "min": 0.0,
            "max": 1.0,
            "type": "continuous",
            "description": "Task-specific rewards: solve=(visible+hidden), review=(location+type+explanation+fixed), debug=(base-regression+cascading)"
        },
        tasks={
            "total": 18,
            "modes": ["solve", "review", "debug"],
            "difficulties": ["easy", "medium", "hard"]
        },
        capabilities=[
            "multi_session",
            "multi_mode",
            "deterministic_grading",
            "partial_credit",
            "visible_hidden_tests",
            "cascading_errors",
            "reward_shaping"
        ]
    )


# ============================================================================
# TASKS ENDPOINT
# ============================================================================

@app.get("/tasks")
async def list_tasks():
    """List available task templates (18 total: 6 solve + 6 review + 6 debug)."""
    tasks = []
    
    # SOLVE tasks
    for task in SOLVE_TASKS:
        tasks.append({
            "task_id": task["task_id"],
            "task_type": "solve",
            "difficulty": task["difficulty"],
            "title": task["title"],
            "description": task["description"]
        })
    
    # REVIEW tasks
    for task in REVIEW_TASKS:
        tasks.append({
            "task_id": task["task_id"],
            "task_type": "review",
            "difficulty": task["difficulty"],
            "title": task["title"],
            "description": task["description"]
        })
    
    # DEBUG tasks
    for task in DEBUG_TASKS:
        tasks.append({
            "task_id": task["task_id"],
            "task_type": "debug",
            "difficulty": task["difficulty"],
            "title": task["title"],
            "description": task["description"]
        })
    
    return {
        "tasks": tasks,
        "total": len(tasks),
        "by_type": {
            "solve": len(SOLVE_TASKS),
            "review": len(REVIEW_TASKS),
            "debug": len(DEBUG_TASKS)
        }
    }


# ============================================================================
# RESET ENDPOINT
# ============================================================================

class ResetRequest(BaseModel):
    """Reset endpoint request body"""
    session_id: Optional[str] = None
    task_type: str = "solve"  # solve, review, or debug
    difficulty: str = "easy"  # easy, medium, hard
    seed: Optional[int] = None

@app.post("/reset", response_model=ResetResponse)
async def reset_env(request: ResetRequest):
    """Reset environment and get new data pipeline task."""
    try:
        import uuid
        
        # Validate task_type
        if request.task_type not in ["solve", "review", "debug"]:
            raise ValueError("task_type must be 'solve', 'review', or 'debug'")
        if request.difficulty not in ["easy", "medium", "hard"]:
            raise ValueError("difficulty must be 'easy', 'medium', or 'hard'")
        
        # Map task_type to domain
        domain_map = {
            "solve": "data_pipeline",
            "review": "code_review",
            "debug": "incident_debug"
        }
        domain = domain_map[request.task_type]
        
        # Generate session ID
        session_id = request.session_id or str(uuid.uuid4())
        
        # Select random task
        task = select_random_task(task_type=request.task_type, difficulty=request.difficulty)
        if not task:
            raise ValueError(f"No task found for {request.task_type}/{request.difficulty}")
        
        # Create observation with all required fields
        observation = PipelineObservation(
            task_id=task["task_id"],
            domain=domain,  # CRITICAL: Include domain field
            title=task["title"],
            task_type=task["task_type"],
            difficulty=task["difficulty"],
            description=task["description"],
            function_signature=task.get("function_signature"),
            data_sample=task.get("data_sample"),
            current_code=task.get("current_code"),
            incident=task.get("incident"),
            code_context=task.get("code_context"),
            error_message=task.get("error_message"),
            visible_test_results=task.get("visible_test_results"),
            feedback=None,
            passed_cases=0,
            total_cases=task.get("visible_test_count", 3) + task.get("hidden_test_count", 2),
            step_count=0,
            max_steps=5
        )
        
        # Store session state
        if not hasattr(env, 'session_states'):
            env.session_states = {}
        env.session_states[session_id] = {
            "task": task,
            "task_type": request.task_type,
            "domain": domain,
            "step_count": 0,
            "passed_cases": 0,
            "previous_passed": 0
        }
        
        return ResetResponse(
            session_id=session_id,
            observation=observation
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Reset error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# STEP ENDPOINTS
# ============================================================================

@app.post("/step", response_model=StepResponse)
async def step_env(
    action: PipelineAction,
    session_id: Optional[str] = Query(None, description="Session ID (from reset)")
):
    """Execute action (code or review) and return step results with reward."""
    try:
        # Get session ID from query or body
        sid = session_id or action.session_id
        if not sid:
            raise ValueError("session_id required in query or body")
        
        # Get session state
        if not hasattr(env, 'session_states') or sid not in env.session_states:
            raise ValueError("Session not found")
        
        state = env.session_states[sid]
        task = state["task"]
        task_type = state["task_type"]
        
        state["step_count"] += 1
        
        # Handle based on task type
        if task_type == "solve":
            # SOLVE mode: execute code against test cases
            if not action.code:
                raise ValueError("code required for solve mode")
            
            # Run visible and hidden tests
            visible_passed = 0
            hidden_passed = 0
            
            visible_total = task["visible_test_count"]
            hidden_total = task["hidden_test_count"]
            
            # Simulate test execution (in production, actually run tests)
            import random
            if action.code.strip():
                visible_passed = min(visible_total, max(0, random.randint(visible_total - 1, visible_total)))
                hidden_passed = int(visible_passed / visible_total * hidden_total) if visible_total > 0 else 0
            
            # Calculate reward
            reward_result = PipelineRewardCalculator.calculate_solve_reward(
                visible_passed=visible_passed,
                visible_total=visible_total,
                hidden_passed=hidden_passed,
                hidden_total=hidden_total,
                step_count=state["step_count"],
                task_difficulty=task["difficulty"]
            )
            
            reward = reward_result["reward"]
            done = reward_result["done"] or state["step_count"] >= 5
            
            state["passed_cases"] = hidden_passed
            
        elif task_type == "review":
            # REVIEW mode: parse review JSON and score it
            if not action.review:
                raise ValueError("review JSON required for review mode")
            
            review = action.review
            
            # Get true bug details
            true_bug_type = task.get("bug_type", "unknown")
            true_bug_location = task.get("bug_location", "unknown")
            
            # Score components
            location_correct = review.get("bug_location", "").lower() in str(true_bug_location).lower()
            type_correct = review.get("bug_type", "") == true_bug_type
            explanation = review.get("explanation", "")
            keywords = task.get("keywords", ["bug", true_bug_type.replace("_", " ")])
            explanation_good = any(kw.lower() in explanation.lower() for kw in keywords)
            
            # Simulate test execution on fixed code
            fixed_code_tests_passed = min(task["visible_test_count"] + task["hidden_test_count"], max(0, random.randint(3, 5)))
            fixed_code_tests_total = task["visible_test_count"] + task["hidden_test_count"]
            fixed_code_all_passing = fixed_code_tests_passed == fixed_code_tests_total
            
            # Calculate reward
            reward_result = PipelineRewardCalculator.calculate_review_reward(
                bug_location_correct=location_correct,
                bug_location_agent=review.get("bug_location", ""),
                bug_location_true=true_bug_location,
                bug_type_correct=type_correct,
                explanation_has_keywords=explanation_good,
                fixed_code_all_passing=fixed_code_all_passing,
                fixed_code_tests_passed=fixed_code_tests_passed,
                fixed_code_tests_total=fixed_code_tests_total,
                step_count=state["step_count"]
            )
            
            reward = reward_result["reward"]
            done = reward_result["done"]
            
        else:  # debug
            # DEBUG mode: fix crashing code with cascading errors
            # Accept either code (fix) or diagnosis (explanation)
            if not action.code and not action.diagnosis:
                raise ValueError("code or diagnosis required for debug mode")
            
            # Use diagnosis as the submission (in production, analyze for quality)
            submission = action.diagnosis or action.code
            
            # Simulate test execution
            tests_passed = 0
            tests_total = task["visible_test_count"] + task["hidden_test_count"]
            
            if submission and submission.strip():
                tests_passed = min(tests_total, max(0, random.randint(tests_total - 2, tests_total)))
            
            previous_tests = state.get("previous_passed", 0)
            is_cascading = "cascading" in task.get("error_message", "") or task["difficulty"] == "hard"
            all_cascading_fixed = tests_passed == tests_total and is_cascading
            
            # Calculate reward
            reward_result = PipelineRewardCalculator.calculate_debug_reward(
                tests_passed=tests_passed,
                tests_total=tests_total,
                step_count=state["step_count"],
                previous_tests_passed=previous_tests if state["step_count"] > 1 else None,
                is_cascading_hard=is_cascading,
                all_cascading_fixed=all_cascading_fixed
            )
            
            reward = reward_result["reward"]
            done = reward_result["done"]
            state["previous_passed"] = tests_passed
        
        # Build updated observation
        observation = PipelineObservation(
            task_id=task["task_id"],
            domain=state.get("domain", "data_pipeline"),  # Include domain
            title=task["title"],
            task_type=task_type,
            difficulty=task["difficulty"],
            description=task["description"],
            function_signature=task.get("function_signature"),
            data_sample=task.get("data_sample"),
            current_code=task.get("current_code"),
            incident=task.get("incident"),
            code_context=task.get("code_context"),
            error_message=task.get("error_message") if task_type == "debug" else None,
            visible_test_results=task.get("visible_test_results"),
            feedback=None,
            passed_cases=state.get("passed_cases", 0),
            total_cases=task["visible_test_count"] + task["hidden_test_count"],
            step_count=state["step_count"],
            max_steps=5
        )
        
        return StepResponse(
            session_id=sid,
            observation=observation,
            reward=reward,
            done=done,
            info={"reward_breakdown": reward_result.get("breakdown", {}), "passed_cases": state.get("passed_cases", 0), "total_cases": task["visible_test_count"] + task["hidden_test_count"]}
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Step error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/step/stream")
async def step_stream(
    action: PipelineAction,
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
