"""
Re-export the FastAPI app from the actual location for OpenEnv compatibility.
"""
import sys
import os
import uvicorn
from envs.code_solver_env.server.app import app

__all__ = ["app"]


def main():
    """Main entry point for running the server."""
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 7860))
    reload = os.getenv("RELOAD", "false").lower() == "true"
    workers = int(os.getenv("WORKERS", "1"))
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        reload=reload,
        workers=workers,
        log_level="info"
    )


if __name__ == "__main__":
    main()
