#!/usr/bin/env python3
"""
APEX Code Solver FastAPI Server Startup

Run with: python run_server.py
"""

import sys
import os
from pathlib import Path

def main():
    """Run the FastAPI server"""
    # Add project root to path
    project_root = Path(__file__).parent
    sys.path.insert(0, str(project_root))

    import uvicorn
    from envs.code_solver_env.server.app import app

    # Configuration
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    reload = os.getenv("RELOAD", "false").lower() == "true"
    workers = int(os.getenv("WORKERS", "1"))

    print("\n" + "=" * 80)
    print("APEX CODE SOLVER - FastAPI Server v2.0.0")
    print("=" * 80)
    print(f"Host: {host}:{port}")
    print(f"Reload: {reload}")
    print(f"Workers: {workers}")
    print()
    print("📖 Interactive docs: http://localhost:{}/docs".format(port))
    print("📖 ReDoc: http://localhost:{}/redoc".format(port))
    print("📖 API Manifest: http://localhost:{}/manifest".format(port))
    print()
    print("Press CTRL+C to stop server")
    print("=" * 80 + "\n")

    # Run with uvicorn
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

    print()
    print("Environment variables:")
    print(f"  API_BASE_URL: {os.getenv('API_BASE_URL', 'not set')}")
    print(f"  MODEL_NAME: {os.getenv('MODEL_NAME', 'not set')}")
    print()
    print("Press CTRL+C to stop")
    print("=" * 70 + "\n")
    
    # Run server
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info",
    )

if __name__ == "__main__":
    main()
