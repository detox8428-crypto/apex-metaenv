"""FastAPI Server for Screen Task Environment"""

from fastapi import FastAPI, HTTPException, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
import uvicorn
from .screen_task_environment import ScreenTaskEnvironment
from ...models import ScreenAction, ScreenObservation, ScreenState


# Initialize environment (single instance for this server)
env = ScreenTaskEnvironment()


# Request/Response models for FastAPI
class ResetRequest(BaseModel):
    pass


class StepRequest(BaseModel):
    action: ScreenAction


class StepResponse(BaseModel):
    observation: ScreenObservation
    reward: float
    done: bool


class StateResponse(BaseModel):
    state: ScreenState


def create_app():
    """Create and configure FastAPI application"""
    app = FastAPI(
        title="Screen Task Environment",
        description="OpenEnv Environment for GUI Interaction Learning",
        version="0.1.0"
    )

    @app.get("/")
    def root():
        """Health check endpoint"""
        return {"status": "ok", "service": "screen_task_env"}

    @app.post("/reset")
    def reset_env(request: ResetRequest = Body(default=ResetRequest())):
        """Reset the environment and return initial observation"""
        try:
            observation = env.reset()
            return JSONResponse(
                status_code=200,
                content={
                    "observation": {
                        "screenshot_b64": observation.screenshot_b64,
                        "task": observation.task,
                        "last_action_result": observation.last_action_result,
                        "step_num": observation.step_num
                    }
                }
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/step")
    def step_env(request: StepRequest):
        """Execute an action and return observation, reward, and done flag"""
        try:
            observation, reward, done = env.step(request.action)
            return JSONResponse(
                status_code=200,
                content={
                    "observation": {
                        "screenshot_b64": observation.screenshot_b64,
                        "task": observation.task,
                        "last_action_result": observation.last_action_result,
                        "step_num": observation.step_num
                    },
                    "reward": reward,
                    "done": done
                }
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/state")
    def get_state():
        """Get current environment state"""
        try:
            state = env.state_property
            return JSONResponse(
                status_code=200,
                content={
                    "state": {
                        "task_id": state.task_id,
                        "task_description": state.task_description,
                        "app_handle": state.app_handle,
                        "is_running": state.is_running
                    }
                }
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.on_event("shutdown")
    def shutdown_event():
        """Clean up when server shuts down"""
        env.close()

    return app


# Create the app instance
app = create_app()


if __name__ == "__main__":
    uvicorn.run(
        "server.app:app",
        host="0.0.0.0",
        port=8000,
        reload=False
    )
