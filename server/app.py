"""
Re-export the FastAPI app from root app.py for OpenEnv compatibility.
"""
import sys
import os
import uvicorn

# Add parent dir so we can import root app.py
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app  # noqa: F401

__all__ = ["app"]


def main():
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 7860))
    workers = int(os.getenv("WORKERS", "1"))
    uvicorn.run("app:app", host=host, port=port, workers=workers, log_level="info")


if __name__ == "__main__":
    main()
