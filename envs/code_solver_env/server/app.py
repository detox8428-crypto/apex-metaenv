"""FastAPI Server for Code Solver Environment"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from .code_solver_environment import CodeSolverEnvironment
from models import CodeSolverAction, CodeSolverObservation


# Initialize environment (single instance)
env = CodeSolverEnvironment()


# Request/Response models
class ResetRequest(BaseModel):
    difficulty: str = None


class StepRequest(BaseModel):
    action: CodeSolverAction


def create_app():
    """Create and configure FastAPI application"""
    app = FastAPI(
        title="Code Solver Environment",
        description="RL Environment for coding problem solving",
        version="0.1.0"
    )

    @app.get("/health")
    def health():
        """Health check endpoint"""
        return {"status": "ok"}

    @app.get("/")
    def root():
        """Root endpoint"""
        return {"service": "code-solver-env", "version": "0.1.0"}

    @app.post("/reset")
    def reset_env(request: ResetRequest = Body(default=ResetRequest())):
        """Reset environment and return initial observation"""
        try:
            observation = env.reset(difficulty=request.difficulty)
            return JSONResponse(
                status_code=200,
                content={
                    "observation": {
                        "problem_id": observation.problem_id,
                        "title": observation.title,
                        "description": observation.description,
                        "function_signature": observation.function_signature,
                        "examples": observation.examples,
                        "constraints": observation.constraints,
                        "difficulty": observation.difficulty,
                        "test_results": observation.test_results,
                        "passed_cases": observation.passed_cases,
                        "total_cases": observation.total_cases,
                        "error_message": observation.error_message
                    }
                }
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/step")
    def step_env(request: StepRequest):
        """Execute code and return results"""
        try:
            action = CodeSolverAction(code=request.action.code)
            observation, reward, done = env.step(action)
            
            return JSONResponse(
                status_code=200,
                content={
                    "observation": {
                        "problem_id": observation.problem_id,
                        "title": observation.title,
                        "description": observation.description,
                        "function_signature": observation.function_signature,
                        "examples": observation.examples,
                        "constraints": observation.constraints,
                        "difficulty": observation.difficulty,
                        "test_results": observation.test_results,
                        "passed_cases": observation.passed_cases,
                        "total_cases": observation.total_cases,
                        "error_message": observation.error_message
                    },
                    "reward": float(reward),
                    "done": done
                }
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/state")
    def get_state():
        """Get current state"""
        try:
            state = env.state
            return JSONResponse(
                status_code=200,
                content={
                    "state": {
                        "problem_id": state.problem_id,
                        "difficulty": state.difficulty,
                        "attempts": state.attempts
                    }
                }
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    return app


# Create the app instance
app = create_app()
